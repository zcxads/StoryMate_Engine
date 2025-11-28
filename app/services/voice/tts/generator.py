import asyncio
from io import BytesIO
import os
import uuid
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime

import boto3
from app.core.config import settings
from app.models.voice.tts import (
    TTSRequest, SingleTTSRequest, TTSResponse, SingleTTSResponse,
    TTSJobStatus, JobStatusResponse, VoiceListResponse, GenderType, GeminiVoiceType,
    PlayTTSRequest
)
import random
import re
from murf import AsyncMurf
import base64
import httpx
from app.repositories.openai_tts import GeminiTTSRepository, OpenAITTSRepository
from app.services.voice.tts.notification import notification_service
from app.utils.process_text import strip_rich_text_tags

# TTS 로깅 설정
from app.utils.logger.setup import setup_logger
import logging

logger = setup_logger('tts_generator', 'logs/tts')

# httpx 로그 비활성화 (INFO 레벨 로그 숨김)
logging.getLogger("httpx").setLevel(logging.WARNING)

MURF_API_KEY = os.getenv("MURF_API_KEY")

# 무음 오디오 파일 NCP URL
SILENT_AUDIO_URL = "storymate-dev/TTS/silent_1sec.mp3"

class TTSService:
    """TTS 생성 비즈니스 로직을 담당하는 Service - 하트비트 개선"""
    
    def __init__(self):
        # mod by LAB (25.08.19) 
        self.gemini_repo = GeminiTTSRepository()
        self.openai_repo = OpenAITTSRepository()
        # mod by LAB (25.08.19) 
        self.jobs: Dict[str, Dict[str, Any]] = {}  # 작업 상태 저장소 (실제로는 Redis 등 사용 권장)
        self.play_jobs: Dict[str, Dict[str, Any]] = {}  # 연극 TTS 작업 상태 저장소
        
        if MURF_API_KEY:
            self.murf_client = AsyncMurf(api_key=MURF_API_KEY)
        else:
            self.murf_client = None
            logger.warning("MURF_API_KEY가 설정되지 않았습니다. MurfAI 기능을 사용할 수 없습니다.")
        self.s3_client = boto3.client(
            service_name=os.getenv("NAVER_SERVICE_NAME"),
            endpoint_url=os.getenv("NAVER_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("ACCESS"),
            aws_secret_access_key=os.getenv("SECRET")
        )
    
    def _ensure_output_directory(self) -> str:
        """출력 디렉토리 생성 및 경로 반환"""
        output_path = os.path.join(os.getcwd(), settings.output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        # 권한 확인 및 설정
        try:
            os.chmod(output_path, 0o777)
        except PermissionError:
            logger.warning(f"⚠️ Warning: Could not set permissions for {output_path}")
            
        return output_path
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    def _ensure_play_ncp_bucket(self, filename: str) -> str:
        """연극 TTS NCP 버킷 경로 반환"""
        bucket_play_folder = settings.naver_bucket_play_folder
        date_folder = datetime.now().strftime("%Y%m%d")
        
        ncp_path = f"{bucket_play_folder}/{date_folder}/{filename}"
        
        return ncp_path
    
    def _select_openai_voice_by_gender(self, gender_hint: Optional[GenderType]) -> str:
        """입력된 성별 힌트에 맞는 OpenAI 기본 보이스 선택"""
        try:
            gender_value = self._get_clean_gender_value(gender_hint) if gender_hint is not None else GenderType.MALE.value
        except Exception:
            gender_value = GenderType.MALE.value
        if gender_value == GenderType.FEMALE.value and settings.openai_female_voices:
            return settings.openai_female_voices[0]
        if gender_value == GenderType.MALE.value and settings.openai_male_voices:
            return settings.openai_male_voices[0]
        # 중성 또는 리스트 비어있을 때의 폴백
        if settings.openai_male_voices:
            return settings.openai_male_voices[0]
        if settings.openai_all_voices:
            return settings.openai_all_voices[0]
        return "echo"
    
    def _get_clean_voice_value(self, voice) -> str:
        """Voice 값에서 실제 문자열 값 추출"""
        if hasattr(voice, 'value'):
            return voice.value
        elif isinstance(voice, str):
            return voice
        else:
            return str(voice)
    
    def _get_clean_gender_value(self, gender_hint) -> str:
        """Gender 힌트에서 실제 문자열 값 추출"""
        if hasattr(gender_hint, 'value'):
            return gender_hint.value
        elif isinstance(gender_hint, str):
            return gender_hint
        else:
            return str(gender_hint)

    def _is_empty_text(self, text: Optional[str]) -> bool:
        """텍스트가 비어있는지 확인"""
        return not text or text.strip() == ""

    def _get_silent_audio_response(self) -> Dict[str, Any]:
        """무음 오디오 응답 반환"""
        logger.info(f"🔇 Empty text detected - returning silent audio URL: {SILENT_AUDIO_URL}")
        return {
            "success": True,
            "file_url": SILENT_AUDIO_URL,
            "message": "Empty text - silent audio returned"
        }
    
    def _generate_filename(self, text_index: int, voice, gender_hint) -> str:
        """파일명 생성 (UUID로 고유성 보장)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 고유성을 위한 UUID 생성 (8자리)
        unique_id = str(uuid.uuid4())[:8]

        # Enum 값을 실제 문자열로 변환
        clean_voice = self._get_clean_voice_value(voice)
        clean_gender = self._get_clean_gender_value(gender_hint)

        # 파일명에 사용할 수 없는 문자 제거
        clean_voice = clean_voice.replace(".", "_").replace("/", "_")
        clean_gender = clean_gender.replace(".", "_").replace("/", "_")

        return f"tts_{text_index:02d}_{clean_voice}_{clean_gender}_{timestamp}_{unique_id}.{settings.audio_format}"
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    def _generate_play_filename(self, text_index: int, voice, gender_hint) -> str:
        """파일명 생성 (UUID로 고유성 보장)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 고유성을 위한 UUID 생성 (8자리)
        unique_id = str(uuid.uuid4())[:8]

        # 파일명에 사용할 수 없는 문자 제거
        clean_voice = voice.replace(".", "_").replace("/", "_")
        clean_gender = gender_hint.replace(".", "_").replace("/", "_")

        return f"play_{text_index:02d}_{clean_voice}_{clean_gender}_{timestamp}_{unique_id}.{settings.audio_format}"
    
    def get_voice_list(self, provider: Optional[str] = None) -> VoiceListResponse:
        """사용 가능한 목소리 목록 반환 (provider에 따라 Gemini/OpenAI 구분)"""
        prov = (provider or "gemini").lower()
        if prov == "openai":
            return VoiceListResponse(
                all_voices=settings.openai_all_voices,
                male_voices=settings.openai_male_voices,
                female_voices=settings.openai_female_voices
            )
        # default gemini
        return VoiceListResponse(
            all_voices=settings.gemini_all_voices,
            male_voices=settings.gemini_male_voices,
            female_voices=settings.gemini_female_voices
        )
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요    
    def get_mapped_conversation_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """생성할 대화 매핑"""
        try:
            logger.info(f"생성할 대화 매핑 시작: {data}")
            title = (data.get("playTitle") or "").strip()
            script = data.get("script") or []
            
            output: List[Dict[str, Any]] = []
            # 타이틀 내래이터 매핑
            if title:
                output.append({"narrator": title})
                
            i = 0
            logger.info(f"스크립트 처리 시작, 총 {len(script)}개 라인")
            
            while i < len(script):
                line = (script[i] or "").strip()
                logger.info(f"라인 {i}: '{line}'")

                # 타이틀 건너뛰기
                if line.startswith("[Title]"):
                    i += 1
                    continue

                # 일반 화자 매핑
                if ":" in line:
                    speaker, text = line.split(":", 1)
                    # Unity rich text 태그 제거 (role에서)
                    clean_speaker = strip_rich_text_tags(speaker.strip())
                    output.append({clean_speaker: text.strip()})

                i += 1
            
            logger.info(f"스크립트 처리 완료, 총 {len(output)}개 항목 생성")
    
            return output
            
        except Exception as e:
            logger.error(f"get_mapped_conversation_list 에러: {e}", exc_info=True)
    
            return []
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    def get_mapped_voice_list(self, items: List[Dict[str, str]], language: str, seed: int | None = None,) -> List[Dict[str, str]]:
        """
        내래이터와 화자를 murfai voice id에 매핑 (언어별 화자 수 제한 적용)
        """
        if seed is not None:
            random.seed(seed)

        # 언어별 최대 화자 수 설정 (narrator 제외) 및 보이스 풀 구성
        male_pool: List[str] = []
        female_pool: List[str] = []

        if language == "ko":
            # 한국어: narrator + speaker1 + speaker2 (총 3명)
            max_speakers = 2
            male_pool = settings.murfai_korean_male_voices or []
            female_pool = settings.murfai_korean_female_voices or []
            narrator_voice = settings.murfai_korean_narrator_voice
        elif language == "ja":
            # 일본어: narrator + speaker1 + speaker2 (총 3명)
            max_speakers = 2
            male_pool = settings.murfai_japanese_male_voices or []
            female_pool = settings.murfai_japanese_female_voices or []
            narrator_voice = settings.murfai_japanese_narrator_voice
        elif language in ["zh", "zh-CN", "zh-TW", "chinese"]:
            # 중국어: narrator + speaker1 + speaker2 (총 3명)
            max_speakers = 2
            male_pool = settings.murfai_chinese_male_voices or []
            female_pool = settings.murfai_chinese_female_voices or []
            narrator_voice = settings.murfai_chinese_narrator_voice
        elif language == "en":
            # 영어: narrator + speaker1~4 (총 5명)
            max_speakers = 4
            male_pool = settings.murfai_english_male_voices or []
            female_pool = settings.murfai_english_female_voices or []
            narrator_voice = settings.murfai_english_narrator_voice
        else:
            # 기본값은 영어 풀 사용
            max_speakers = 4
            male_pool = settings.murfai_english_male_voices or []
            female_pool = settings.murfai_english_female_voices or []
            narrator_voice = settings.murfai_english_narrator_voice

        speaker_to_voice: Dict[str, str] = {}
        output: List[Dict[str, str]] = []

        # 금지된 role 이름 목록 (여러 명이 동시에 말하는 경우)
        forbidden_roles = {
            "family", "everyone", "all", "group", "chorus",
            "가족", "모두", "전체", "children", "people", "crowd",
            "together", "함께", "全員", "みんな"
        }

        for item in items:
            if not item:
                continue
            role, text = next(iter(item.items()))
            role_l = role.lower().strip()

            # 금지된 role 감지 및 로그
            if role_l in forbidden_roles:
                logger.warning(f"🚫 금지된 role 감지: '{role}' - 여러 명이 동시에 말하는 role은 허용되지 않습니다.")
                logger.warning(f"   해당 대사는 건너뜁니다: '{text[:50]}...'")
                continue

            if role_l == "narrator":
                output.append({"voice_id": narrator_voice, "text": text, "role": role})
                continue

            m = re.fullmatch(r"(speaker)(\d+)", role_l)
            if m:
                label = m.group(0)       # 예: "speaker1"
                idx = int(m.group(2))    # 숫자

                # 언어별 최대 화자 수 제한 검증
                if idx > max_speakers:
                    logger.warning(f"⚠️ 화자 수 제한 초과 감지: {role} (언어: {language}, 최대: speaker{max_speakers})")
                    logger.warning(f"   자동으로 speaker{max_speakers}로 매핑합니다.")
                    # 초과된 화자는 마지막 허용 화자로 매핑
                    label = f"speaker{max_speakers}"
                    idx = max_speakers

                if label not in speaker_to_voice:
                    if language == "en":
                        # 영어 연극: speaker1-4가 각각 다른 목소리를 가지도록 순서대로 할당
                        # 사용 가능한 모든 목소리를 순서대로 할당
                        all_voices = (male_pool or []) + (female_pool or [])
                        if all_voices:
                            # speaker 번호에 따라 순서대로 할당 (1-based index)
                            voice_index = (idx - 1) % len(all_voices)
                            selected_voice = all_voices[voice_index]
                            gender_type = "남성" if all_voices[voice_index] in (male_pool or []) else "여성"
                        else:
                            # 목소리가 없으면 내레이터로 폴백
                            selected_voice = narrator_voice
                            gender_type = "내레이터"
                    else:
                        # 다른 언어: speaker1=남성, speaker2=여성
                        # speaker1 (idx=1, 홀수) → male_pool
                        # speaker2 (idx=2, 짝수) → female_pool
                        pool = male_pool if (idx % 2 == 1) else female_pool
                        gender_type = "남성" if (idx % 2 == 1) else "여성"

                        # 풀 비어있으면 사용 가능한 풀 중 하나 사용
                        if not pool:
                            pool = male_pool if male_pool else female_pool
                        # 여전히 없으면 내레이터 보이스를 폴백
                        choice_pool = pool if pool else [narrator_voice]
                        selected_voice = random.choice(choice_pool)
                    
                    speaker_to_voice[label] = selected_voice
                    
                    # 디버깅을 위한 로그 추가
                    logger.info(f"🎭 Speaker {label} ({gender_type}) → Voice: {selected_voice}")

                output.append({"voice_id": speaker_to_voice[label], "text": text, "role": role})
            else:
                # 예외 라벨 → 사용 가능한 풀에서 랜덤 선택 (없으면 내레이터로 폴백)
                combined_pool = (female_pool or []) + (male_pool or [])
                chosen = random.choice(combined_pool) if combined_pool else narrator_voice
                output.append({"voice_id": chosen, "text": text, "role": role})

        # 최종 화자 수 검증 로그
        unique_speakers = {k for k in speaker_to_voice.keys() if k.startswith("speaker")}
        if unique_speakers:
            logger.info(f"✅ 화자 매핑 완료 (언어: {language}): {len(unique_speakers)}명 (최대: {max_speakers}명)")
            logger.info(f"   화자 목록: {sorted(unique_speakers)}")

        return output
    
    async def test_openai_connection(self) -> bool:
        """OpenAI API 연결 테스트"""
        return await self.gemini_repo.test_api_connection()
    
    async def generate_single_tts(self, request: SingleTTSRequest) -> SingleTTSResponse:
        """단일 TTS 파일 생성"""

        try:
            # 빈 텍스트 확인
            if self._is_empty_text(request.text):
                silent_response = self._get_silent_audio_response()
                return SingleTTSResponse(
                    success=True,
                    message=silent_response["message"],
                    filename="silent_1sec.mp3",
                    file_path=None,
                    ncp_url=silent_response["file_url"],
                    duration=1.0
                )

            output_dir = self._ensure_output_directory()

            # 고유성을 위한 UUID 생성 (8자리)
            unique_id = str(uuid.uuid4())[:8]
            
            # 파일명 생성 (Enum 값 처리)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_gender = self._get_clean_gender_value(request.gender_hint)

            # Rich Text 태그 제거
            clean_text = strip_rich_text_tags(request.text)

            # TTS provider 선택 (config의 default_tts_provider 사용)
            provider = settings.default_tts_provider.lower()
            logger.info(f"🎵 TTS 생성 시작 - Provider: {provider}, Gender: {clean_gender}")

            # Provider에 따라 음성 선택 및 TTS 생성
            if provider == "openai":
                # OpenAI: 성별에 맞는 음성 자동 선택
                voice = self._select_openai_voice_by_gender(request.gender_hint)
                filename = f"single_{voice}_{clean_gender}_{timestamp}_{unique_id}.{settings.audio_format}"
                file_path = os.path.join(output_dir, filename)

                success, ncp_url = await self.openai_repo.generate_tts(
                    text=clean_text,
                    voice=voice,
                    filename=file_path
                )
            else:  # gemini (기본값)
                # Gemini: 요청된 voice 사용 또는 성별에 맞는 기본 음성 선택
                if request.voice:
                    voice = self._get_clean_voice_value(request.voice)
                else:
                    # 성별에 맞는 Gemini 음성 선택
                    if clean_gender == GenderType.FEMALE.value and settings.gemini_female_voices:
                        voice = settings.gemini_female_voices[0]
                    elif clean_gender == GenderType.MALE.value and settings.gemini_male_voices:
                        voice = settings.gemini_male_voices[0]
                    else:
                        voice = GeminiVoiceType.get_default().value

                filename = f"single_{voice}_{clean_gender}_{timestamp}_{unique_id}.{settings.audio_format}"
                file_path = os.path.join(output_dir, filename)

                success, ncp_url, is_rate_limit = await self.gemini_repo.generate_tts(
                    text=clean_text,
                    voice=voice,
                    filename=file_path,
                    gender_hint=request.gender_hint
                )
            
            if success:
                # MP3 파일의 duration 계산
                duration = self._get_mp3_duration(file_path) if file_path else None

                # NCP 업로드 성공 후 로컬 파일 삭제
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ 로컬 파일 삭제 완료: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ 로컬 파일 삭제 실패: {file_path} - {str(e)}")

                return SingleTTSResponse(
                    success=True,
                    message="TTS 파일이 성공적으로 생성되었습니다.",
                    filename=filename,
                    file_path=file_path,
                    # download_url=f"/api/v1/tts/download/{filename}",
                    ncp_url=ncp_url,
                    duration=duration
                )
            else:
                return SingleTTSResponse(
                    success=False,
                    message="TTS 파일 생성에 실패했습니다."
                )
                
        except Exception as e:
            logger.error(f"❌ Single TTS generation error: {str(e)}")
            return SingleTTSResponse(
                success=False,
                message=f"TTS 생성 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def generate_batch_tts(self, request: TTSRequest) -> TTSResponse:
        """배치 TTS 파일 생성 - 하트비트 개선"""

        # 작업 ID 생성
        job_id = str(uuid.uuid4())

        # 설정에서 TTS 제공자 확인
        tts_provider = settings.default_tts_provider.lower()
        logger.info(f"🔧 배치 TTS 제공자: {tts_provider}")

        if request.voices and len(request.voices) > 0:
            voices_to_use = [self._get_clean_voice_value(v) for v in request.voices]
            logger.debug(f"🔧 DEBUG: 사용자 지정 목소리 사용 - {voices_to_use}")
        else:
            # 제공자에 따라 기본 목소리 선택
            if tts_provider == "murf":
                # Murf 기본 목소리 (한국어)
                voices_to_use = [settings.murfai_korean_female_voices[0] if settings.murfai_korean_female_voices else "ko-KR-gyeong"]
                logger.debug(f"🔧 DEBUG: Murf 기본 목소리 사용 - {voices_to_use}")
            elif tts_provider == "openai":
                # OpenAI 기본 목소리
                voices_to_use = ["echo"]
                logger.debug(f"🔧 DEBUG: OpenAI 기본 목소리 사용 - {voices_to_use}")
            else:  # gemini (기본값)
                # Gemini 기본 목소리
                voices_to_use = [GeminiVoiceType.get_default().value]
                logger.debug(f"🔧 DEBUG: Gemini 기본 목소리 사용 - {voices_to_use}")
        
        # 성별 힌트 설정 - 입력된 힌트를 패턴으로 반복 적용
        if request.gender_hints:
            gender_hints = []
            for i in range(len(request.texts)):
                # 입력된 gender_hints를 순환하여 적용 (예: ["남자", "여자"] → "남자", "여자", "남자", "여자", ...)
                hint_index = i % len(request.gender_hints)
                gender_hints.append(request.gender_hints[hint_index])
        else:
            # 힌트가 전달되지 않은 경우 모델에 정의된 기본값 사용
            gender_hints = [GenderType.get_default()] * len(request.texts)
            logger.debug(f"🔧 DEBUG: 기본 성별 사용 - {[g.value for g in gender_hints]}")
        
        # 총 파일 수 계산 (텍스트 개수 = 파일 개수, 각 텍스트마다 하나의 voice와 gender_hint 사용)
        total_files = len(request.texts)

        # Murf 사용 시 언어 설정 (request에 language가 있으면 사용, 없으면 기본값 "ko")
        language = getattr(request, 'language', 'ko') if hasattr(request, 'language') else 'ko'

        # 작업 상태 초기화
        self.jobs[job_id] = {
            "status": TTSJobStatus.PENDING,
            "total_files": total_files,
            "completed_files": 0,
            "failed_files": 0,
            "files": [],
            "start_time": datetime.now(),
            "texts": request.texts,
            "voices": voices_to_use,
            "gender_hints": gender_hints,
            "batch_size": request.batch_size,
            "tts_provider": tts_provider,  # TTS 제공자 저장
            "language": language,  # Murf 사용 시 필요한 언어 정보
            "paused": False,  # 일시 중단 상태
            "connection_checks": 0,  # 연결 확인 횟수
            "last_connection_check": datetime.now()
        }
        
        # 백그라운드에서 TTS 생성 실행
        asyncio.create_task(self._process_batch_tts(job_id))
        
        return TTSResponse(
            job_id=job_id,
            status=TTSJobStatus.PENDING,
            message="TTS 배치 작업이 시작되었습니다.",
            total_files=total_files,
            completed_files=0
        )
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    async def generate_play_tts(self, request: PlayTTSRequest) -> TTSResponse:
        """연극 TTS 파일 생성 (Murf 전용)"""
        # 작업 ID 생성
        job_id = str(uuid.uuid4())
        total_files = len(request.script)

        logger.info(f"🎭 연극 TTS 배치 작업 시작: {job_id} (Murf TTS)")
        
        # title, script 파싱 후, 리스트 생성
        request_dict = request.model_dump() if hasattr(request, 'model_dump') else request.dict()
        conversation_list = self.get_mapped_conversation_list(request_dict)
        
        items = self.get_mapped_voice_list(conversation_list, request.language)
        
        logger.info(f"voice mapping: {items}")
        
        texts = [it["text"] for it in items]
        voices = [it["voice_id"] for it in items]
        roles = [it["role"] for it in items]
        total_files = len(texts)
        batch_size = 3

        self.jobs[job_id] = {
            "status": TTSJobStatus.PENDING,
            "total_files": total_files,
            "completed_files": 0,
            "failed_files": 0,
            "files": [],
            "start_time": datetime.now(),
            "texts": texts,
            "roles": roles,
            "voices": voices,
            "language": request.language,
            "batch_size": batch_size,
            "paused": False,
            "connection_checks": 0,
            "last_connection_check": datetime.now(),
        }
        
        asyncio.create_task(self._process_play_tts(job_id))
        
        return TTSResponse(
            job_id=job_id,
            status=TTSJobStatus.PENDING,
            message="연극 TTS 배치 작업이 시작되었습니다.",
            total_files=total_files,
            completed_files=0
        )
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    async def _process_batch_tts(self, job_id: str):
        """배치 TTS 생성 처리 (연결 상태 확인 및 하트비트 개선)"""
        
        job = self.jobs[job_id]
        job["status"] = TTSJobStatus.PROCESSING
        
        # 전체 처리 시작 시간 기록
        total_start_time = datetime.now()
        logger.info(f"🚀 전체 배치 TTS 처리 시작: {total_start_time.strftime('%H:%M:%S.%f')[:-3]} (Job ID: {job_id})")
        
        # 처리 시작 알림
        await self._notify_job_status_change(job_id)
        
        output_dir = self._ensure_output_directory()
        
        try:
            texts = job["texts"]
            voices = job["voices"]  # 이미 문자열로 변환됨
            gender_hints = job["gender_hints"]
            batch_size = job["batch_size"]
            
            # 모든 작업을 미리 생성
            tasks = []
            
            # 각 텍스트마다 voices 중 하나를 순환하여 선택
            for text_idx, (text, gender_hint) in enumerate(zip(texts, gender_hints), 1):
                # 연결 상태 논블로킹 확인 - 연결이 없어도 TTS 작업은 계속 진행
                await notification_service.has_active_connections(job_id)

                # 작업이 일시 중단되었는지 확인
                if job.get("paused", False):
                    logger.info(f"⏸️ Job {job_id} is manually paused, waiting for resume...")
                    await self._wait_for_resume(job_id)

                # 빈 텍스트 확인 - 무음 파일 정보 설정 (순서 유지를 위해 task로 처리)
                if self._is_empty_text(text):
                    voice_index = (text_idx - 1) % len(voices)
                    voice = voices[voice_index]

                    logger.info(f"🔇 빈 텍스트 감지 (배치 TTS) - 무음 파일 사용 예정: 인덱스 {text_idx}, Voice: {voice}")

                    task_info = {
                        "text_index": text_idx,
                        "voice": voice,
                        "filename": "silent_1sec.mp3",
                        "file_path": None,
                        "text": text,
                        "gender_hint": self._get_clean_gender_value(gender_hint),
                        "status": "pending"
                    }

                    job["files"].append(task_info)

                    # 무음 파일도 순서를 유지하기 위해 비동기 태스크로 처리
                    async def process_silent_file():
                        task_info["status"] = "processing"
                        logger.info(f"🔇 무음 파일 처리 시작: 인덱스 {text_idx}")

                        # 순서대로 처리하기 위한 약간의 지연 (실제 TTS처럼 동작)
                        await asyncio.sleep(0.1)

                        task_info["status"] = "completed"
                        task_info["end_time"] = datetime.now().isoformat()
                        task_info["ncp_url"] = SILENT_AUDIO_URL
                        task_info["duration"] = 1.0
                        job["completed_files"] += 1

                        # 파일 완료 알림 (연결이 있을 때만)
                        if await notification_service.has_active_connections(job_id):
                            await notification_service.notify_job_progress(job_id, {
                                "filename": task_info["filename"],
                                "status": "completed",
                                "ncp_url": SILENT_AUDIO_URL,
                                "message": "Empty text - silent audio returned"
                            })

                        logger.info(f"✅ 무음 파일 처리 완료: 인덱스 {text_idx}")

                    tasks.append(process_silent_file())
                    continue

                voice_index = (text_idx - 1) % len(voices)
                voice = voices[voice_index]

                filename = self._generate_filename(text_idx, voice, gender_hint)
                file_path = os.path.join(output_dir, filename)

                task_info = {
                    "text_index": text_idx,
                    "voice": voice,
                    "filename": filename,
                    "file_path": file_path,
                    "text": text,
                    "gender_hint": self._get_clean_gender_value(gender_hint),
                    "status": "pending"
                }

                job["files"].append(task_info)

                task = self._generate_single_file(
                    text, voice, file_path, gender_hint, task_info, job_id
                )
                tasks.append(task)
            
            # 배치 크기로 나누어 처리 (최적화된 버전)
            logger.info(f"🚀 배치 처리 시작 - 총 {len(tasks)}개 작업을 {batch_size}개씩 처리")
            
            for batch_idx, i in enumerate(range(0, len(tasks), batch_size)):
                batch = tasks[i:i+batch_size]
                batch_start_time = datetime.now()
                logger.info(f"📦 배치 {batch_idx + 1}/{(len(tasks) + batch_size - 1) // batch_size} 시작 ({len(batch)}개 파일)")
                
                # 백그라운드 연결 모니터링 (성능 최적화)
                if batch_idx == 0:
                    # 첫 번째 배치에서는 동기적으로 확인
                    await self._perform_connection_health_check(job_id)
                    logger.info(f"⏱️ 첫 배치 연결 확인 완료")
                else:
                    # 후속 배치들은 백그라운드에서 비동기 모니터링
                    asyncio.create_task(self._background_connection_monitor(job_id, batch_idx))
                
                # 배치 실행
                batch_execution_start = datetime.now()
                results = await asyncio.gather(*batch, return_exceptions=True)
                batch_execution_duration = (datetime.now() - batch_execution_start).total_seconds()
                
                batch_end_time = datetime.now()
                total_batch_duration = (batch_end_time - batch_start_time).total_seconds()
                
                # 배치 성능 분석
                if total_batch_duration > 3.0:
                    logger.warning(f"⚠️ 배치 {batch_idx + 1} 지연 감지: {total_batch_duration:.3f}초 (임계값: 3초)")
                    # 개별 태스크 결과 분석
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"   • 태스크 {i+1}: 에러 - {str(result)}")
                        else:
                            logger.info(f"   • 태스크 {i+1}: 정상 완료")
                
                logger.info(f"✅ 배치 {batch_idx + 1} 완료 - 실행: {batch_execution_duration:.3f}초, 전체: {total_batch_duration:.3f}초")
                
                # 배치 완료 후 진행상황 알림 (동기 대기로 안정성 확보)
                await self._notify_job_status_change(job_id)
                
                # 모든 배치 후 대기 (안정성 우선) - 원래 메서드 사용
                await self._smart_delay_with_connection_check(job_id, 2.0)
            
            job["status"] = TTSJobStatus.COMPLETED
            job["end_time"] = datetime.now()
            
            # 전체 처리 시간 계산 및 로그 출력
            total_duration = (job["end_time"] - total_start_time).total_seconds()
            success_rate = (job["completed_files"] / (job["completed_files"] + job["failed_files"]) * 100) if (job["completed_files"] + job["failed_files"]) > 0 else 0
            
            logger.info(f"✅ 전체 배치 TTS 처리 완료!")
            logger.info(f"📊 처리 시간 통계:")
            logger.info(f"   • 총 처리 시간: {total_duration:.3f}초")
            logger.info(f"   • 완료 파일: {job['completed_files']}개")
            logger.info(f"   • 실패 파일: {job['failed_files']}개")
            logger.info(f"   • 성공률: {success_rate:.1f}%")
            logger.info(f"   • 파일당 평균 시간: {total_duration/job['total_files']:.3f}초")
            
            # 최종 완료 알림
            await self._notify_job_completion(job_id)
            
        except Exception as e:
            job["status"] = TTSJobStatus.FAILED
            job["end_time"] = datetime.now()
            job["error"] = str(e)
            
            # 실패 시에도 처리 시간 통계 출력
            total_duration = (job["end_time"] - total_start_time).total_seconds()
            
            logger.error(f"❌ 배치 TTS 처리 실패!")
            logger.error(f"📊 실패 시점 통계:")
            logger.error(f"   • 처리된 시간: {total_duration:.3f}초")
            logger.error(f"   • 완료 파일: {job['completed_files']}개")
            logger.error(f"   • 실패 파일: {job['failed_files']}개")
            logger.error(f"   • 오류: {str(e)}")
            
            # 실패 알림
            await self._notify_job_completion(job_id)
            
    # murf 전용 연극 대본 TTS 생성 워커
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    async def _process_play_tts(self, job_id: str):
        try:
            job = self.jobs[job_id]
            job["status"] = TTSJobStatus.PROCESSING
            await self._notify_job_status_change(job_id)

            logger.info(f"play job: {job}")
        except KeyError as e:
            logger.error(f"Job {job_id} not found in self.jobs: {e}")
            return
        except Exception as e:
            logger.error(f"Error in _process_play_tts: {e}", exc_info=True)
            return
        
        # output_dir = self._ensure_output_directory()
        texts = job["texts"]
        voices = job["voices"]
        roles = job["roles"]
        batch_size = job["batch_size"]
        language = job["language"]

        try:
            tasks = []
            for idx, (text, voice_id, role) in enumerate(zip(texts, voices, roles), 1):
                # 빈 텍스트 확인 - 무음 파일 정보 설정 (순서 유지를 위해 task로 처리)
                if self._is_empty_text(text):
                    logger.info(f"🔇 빈 텍스트 감지 (연극 TTS) - 무음 파일 사용 예정: 인덱스 {idx}, Voice: {voice_id}")

                    if (voice_id in settings.murfai_english_female_voices or
                        voice_id in settings.murfai_korean_female_voices or
                        voice_id in settings.murfai_japanese_female_voices or
                        voice_id in settings.murfai_chinese_female_voices):
                        gender_hint = GenderType.FEMALE
                    else:
                        gender_hint = GenderType.MALE

                    task_info = {
                        "text_index": idx,
                        "voice": voice_id,
                        "filename": "silent_1sec.mp3",
                        "file_path": None,
                        "text": text,
                        "role": role,
                        "gender_hint": gender_hint,
                        "status": "pending",
                        "language": language
                    }

                    job["files"].append(task_info)

                    # 무음 파일도 순서를 유지하기 위해 비동기 태스크로 처리
                    async def process_silent_play_file():
                        task_info["status"] = "processing"
                        logger.info(f"🔇 무음 파일 처리 시작 (연극): 인덱스 {idx}")

                        # 순서대로 처리하기 위한 약간의 지연
                        await asyncio.sleep(0.1)

                        task_info["status"] = "completed"
                        task_info["end_time"] = datetime.now().isoformat()
                        task_info["ncp_url"] = SILENT_AUDIO_URL
                        task_info["duration"] = 1.0
                        job["completed_files"] += 1

                        logger.info(f"✅ 무음 파일 처리 완료 (연극): 인덱스 {idx}")

                    tasks.append(process_silent_play_file())
                    continue

                if (voice_id in settings.murfai_english_female_voices or
                    voice_id in settings.murfai_korean_female_voices or
                    voice_id in settings.murfai_japanese_female_voices or
                    voice_id in settings.murfai_chinese_female_voices):
                    gender_hint = GenderType.FEMALE
                else:
                    gender_hint = GenderType.MALE

                filename = self._generate_play_filename(idx, voice_id, gender_hint)
                file_path = self._ensure_play_ncp_bucket(filename)

                task_info = {
                    "text_index": idx,
                    "voice": voice_id,
                    "filename": filename,
                    "file_path": file_path,
                    "text": text,
                    "role": role,
                    "gender_hint": gender_hint,
                    "status": "pending",
                    "language": language,
                }
                job["files"].append(task_info)

                # 연극 TTS는 항상 Murf 사용
                tasks.append(self._process_single_murf(job_id, text, voice_id, file_path, task_info))

            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                await asyncio.gather(*batch, return_exceptions=True)
                await self._notify_job_status_change(job_id)

            job["status"] = TTSJobStatus.COMPLETED
            job["end_time"] = datetime.now()
            await self._notify_job_completion(job_id)

        except Exception as e:
            logger.error(f"Error processing play TTS job {job_id}: {e}", exc_info=True)
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = TTSJobStatus.FAILED
                self.jobs[job_id]["end_time"] = datetime.now()
                self.jobs[job_id]["error"] = str(e)
                await self._notify_job_completion(job_id)
               
    async def _process_single_murf(
        self,
        job_id: str,
        text: str,
        voice_id: str,
        file_path: str,
        task_info: Dict[str, Any],
    ):
        job = self.jobs[job_id]
        task_info["status"] = "processing"

        # 문장별 생성 시간 추적 시작
        sentence_start_time = datetime.now()
        logger.info(f"⏱️ Murf TTS 생성 시작 (문장 {task_info['text_index']}): {text[:50]}...")

        # Rich Text 태그 제거
        clean_text = strip_rich_text_tags(text)

        try:
            success, remote_url, duration = await self._murf_generate(text=clean_text, voice_id=voice_id, file_path=file_path, language=task_info["language"])

            # 문장별 생성 시간 계산 및 로그
            sentence_duration = (datetime.now() - sentence_start_time).total_seconds()

            if success:
                task_info["status"] = "completed"
                task_info["end_time"] = datetime.now().isoformat()
                task_info["ncp_url"] = remote_url
                task_info["generation_time"] = sentence_duration
                # Duration 추가
                if duration:
                    task_info["duration"] = duration
                job["completed_files"] += 1

                logger.info(f"✅ Murf TTS 생성 완료 (문장 {task_info['text_index']}): {sentence_duration:.3f}초 - {text[:50]}...")
            else:
                task_info["status"] = "failed"
                task_info["end_time"] = datetime.now().isoformat()
                task_info["generation_time"] = sentence_duration
                job["failed_files"] += 1

                logger.error(f"❌ Murf TTS 생성 실패 (문장 {task_info['text_index']}): {sentence_duration:.3f}초 - {text[:50]}...")
        except Exception as e:
            sentence_duration = (datetime.now() - sentence_start_time).total_seconds()
            task_info["status"] = "failed"
            task_info["end_time"] = datetime.now().isoformat()
            task_info["error"] = str(e)
            task_info["generation_time"] = sentence_duration
            job["failed_files"] += 1

            logger.error(f"❌ Murf TTS 생성 예외 (문장 {task_info['text_index']}): {sentence_duration:.3f}초 - {str(e)} - {text[:50]}...")
    
    # TODO: 기존 TTS와 병합 혹은 리팩터링 필요
    async def _murf_generate(self, text: str, voice_id: str, file_path: str, language: str) -> tuple[bool, Optional[str], Optional[float]]:
        log_prefix = f"Content: {text}, Voice: {voice_id}"
        logger.info(f"TTS 요청 (Murf) - {log_prefix}")

        if not self.murf_client:
            logger.error("MurfAI 클라이언트가 초기화되지 않았습니다. MURF_API_KEY를 확인하세요.")
            return False, None, None

        language_code_map_for_murf = {
                'zh-CN': 'zh-CN', 'zh': 'zh-CN', 'zh-HK': 'zh-CN', 'zh-TW': 'zh-CN', 'chinese': 'zh-CN',
                'ko': 'ko-KR', 'ko-KR': 'ko-KR', 'korean': 'ko-KR',
                'ja': 'ja-JP', 'ja-JP': 'ja-JP', 'japanese': 'ja-JP',
                'en': 'en-US', 'en-US': 'en-US', 'en-UK': 'en-GB', 'english': 'en-US',
                'es': 'es-MX', 'id': 'hi-IN', 'hi': 'hi-IN', 'fr': 'fr-FR', 'de': 'de-DE', 'it': 'it-IT'
            }
        locale = language_code_map_for_murf.get(language.lower() if language else 'en', 'en-US')

        try:
            text = ' '.join(text.split()).replace('\\"', '"')
            max_text_length = 3000                  #api 요청 당 최대 3000자 입력 가능
            if len(text) > max_text_length:
                logger.warning(f"텍스트 길이 초과로 자름 - {log_prefix}")
                text = text[:max_text_length]

            async with asyncio.Semaphore(1):
                max_attempts = 5
                attempt = 0
                last_error = None
                audio_data = None

                while attempt < max_attempts:
                    attempt += 1
                    try:
                        # API 호출 시간 추적
                        api_call_start = datetime.now()
                        logger.info(f"🌐 Murf API 호출 시작 (시도 {attempt}/{max_attempts})")

                        # API 호출에만 타임아웃 적용 (30초)
                        try:
                            async with asyncio.timeout(30):
                                response = await self.murf_client.text_to_speech.generate(
                                    multi_native_locale=locale,
                                    text=text,
                                    voice_id=voice_id,
                                    encode_as_base_64=False,
                                    style="Conversational",
                                    format="MP3"
                                )
                        except asyncio.TimeoutError:
                            api_call_duration = (datetime.now() - api_call_start).total_seconds()
                            logger.error(f"❌ Murf API 호출 자체가 타임아웃 (30초)")
                            logger.error(f"   • 실제 소요 시간: {api_call_duration:.3f}초")
                            logger.error(f"   • 텍스트 길이: {len(text)}자")
                            logger.error(f"   • 원인: Murf 서버 응답 지연 또는 네트워크 문제")
                            raise

                        api_call_duration = (datetime.now() - api_call_start).total_seconds()
                        logger.info(f"✅ Murf API 호출 완료: {api_call_duration:.3f}초")

                        # 응답 데이터 처리 시작
                        current_audio_data = None

                        # 1단계: base64 인코딩된 오디오 확인
                        encoded_audio = getattr(response, "encoded_audio", None)
                        if encoded_audio:
                            current_audio_data = base64.b64decode(encoded_audio)
                        else:
                            # 2단계: audio_file URL 다운로드
                            audio_url = getattr(response, "audio_file", None)
                            if not audio_url and isinstance(response, dict):
                                audio_url = response.get("audio_file")

                            if isinstance(audio_url, str) and audio_url.startswith("http"):
                                try:
                                    async with asyncio.timeout(60):
                                        async with httpx.AsyncClient() as client:
                                            r = await client.get(audio_url, timeout=60)
                                            r.raise_for_status()
                                            current_audio_data = r.content
                                except asyncio.TimeoutError:
                                    raise ValueError(f"Audio file 다운로드 타임아웃: {audio_url}")

                        # 3단계: 최종 검증
                        if not isinstance(current_audio_data, (bytes, bytearray)):
                            logger.error(f"❌ 오디오 데이터 획득 실패 - response 타입: {type(response)}")
                            raise ValueError(f"Murf 응답에서 오디오 바이트를 얻지 못함 (타입: {type(current_audio_data)})")

                        # 성공: 오디오 데이터를 받았으면 루프 종료
                        logger.info(f"✅ TTS 생성 성공 (시도 {attempt}/{max_attempts}) - {log_prefix}")
                        break

                    except asyncio.TimeoutError:
                        last_error = asyncio.TimeoutError("API 호출 타임아웃 (30초)")
                        reason = "API 타임아웃 (30초)"
                        logger.warning(f"⚠️ TTS 재시도 ({attempt}/{max_attempts}) - {log_prefix}. 사유: {reason}")
                        if attempt >= max_attempts: break
                        await asyncio.sleep(random.uniform(1, 3))
                        continue
                    except Exception as e:
                        last_error = e
                        reason = f"API 오류: {str(e)}"
                        logger.warning(f"⚠️ TTS 재시도 ({attempt}/{max_attempts}) - {log_prefix}. 사유: {reason}")
                        if attempt >= max_attempts: break
                        await asyncio.sleep(random.uniform(1, 3) * attempt)
                        continue

                if current_audio_data is None:
                    logger.error(f"TTS 최종 실패 (Murf) - {log_prefix}. 마지막 오류: {last_error}")
                    return (False, None, None)

                try:
                    # Gemini와 동일한 NCP 경로 생성: TTS/20250110/filename.mp3
                    bucket_name = settings.naver_bucket_name
                    filename = os.path.basename(file_path)
                    date_folder = datetime.now().strftime("%Y%m%d")
                    ncp_path = f"{settings.naver_bucket_tts_folder}/{date_folder}/{filename}"

                    # Duration 계산을 위해 임시로 로컬 파일 저장
                    temp_file_path = None
                    duration = None
                    try:
                        # 로컬에 임시 저장 (duration 계산용)
                        temp_file_path = file_path  # 이미 로컬 경로가 제공됨
                        with open(temp_file_path, 'wb') as f:
                            f.write(current_audio_data)

                        # Duration 계산
                        duration = self._get_mp3_duration(temp_file_path)
                        logger.info(f"🎵 MP3 duration: {duration:.2f}초" if duration else "⚠️ Duration 계산 실패")
                    except Exception as duration_error:
                        logger.warning(f"⚠️ Duration 계산 실패: {str(duration_error)}")

                    # S3에 업로드 (public-read ACL 적용)
                    upload_start = datetime.now()
                    self.s3_client.upload_fileobj(
                        BytesIO(current_audio_data),
                        bucket_name,
                        ncp_path,
                        ExtraArgs={'ACL': 'public-read'}
                    )
                    upload_duration = (datetime.now() - upload_start).total_seconds()

                    # 최종 URL 생성 (Gemini와 동일한 포맷)
                    final_url = f"{bucket_name}/{ncp_path}"

                    # Gemini와 동일한 로그 포맷
                    logger.info(f"✅ Successfully uploaded to NCP: {final_url}")
                    logger.info(f"☁️ NCP 업로드: {upload_duration:.3f}초")
                    logger.info(f"TTS 성공 (Murf) - {log_prefix}, URL: {final_url}")

                    # 로컬 임시 파일 삭제
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                            logger.info(f"🗑️ 로컬 파일 삭제 완료: {temp_file_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ 로컬 파일 삭제 실패: {temp_file_path} - {str(e)}")

                    return (True, final_url, duration)
                except Exception as s3_error:
                    logger.error(f"S3 업로드 실패 - {log_prefix}. 오류: {str(s3_error)}")
                    return (False, None, None)
            
        except Exception as e:
            logger.exception(f"Murf TTS 처리 중 심각한 오류 - {log_prefix}. 오류: {str(e)}")
            return (False, None, None)
    
    async def _check_and_wait_for_connections(self, job_id: str, max_wait_time: int = 30) -> bool:
        """연결 상태 확인 및 복구 대기"""
        job = self.jobs[job_id]
        
        if await notification_service.has_active_connections(job_id):
            return True
        
        logger.warning(f"⚠️ No active connections for job {job_id}, waiting for reconnection...")
        job["paused"] = True
        
        # 최대 대기 시간 동안 연결 복구 대기
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < max_wait_time:
            await asyncio.sleep(2)  # 2초마다 확인
            
            if await notification_service.has_active_connections(job_id):
                logger.info(f"✅ Connection restored for job {job_id}")
                job["paused"] = False
                return True
        
        logger.warning(f"⏰ Connection wait timeout for job {job_id}, proceeding without active connections")
        job["paused"] = False
        return False
    
    async def _wait_for_resume(self, job_id: str):
        """작업 재개 대기"""
        job = self.jobs[job_id]
        
        while job.get("paused", False):
            await asyncio.sleep(1)
            
            # 연결이 복구되면 자동으로 재개
            if await notification_service.has_active_connections(job_id):
                job["paused"] = False
                logger.info(f"▶️ Job {job_id} resumed due to connection recovery")
                break
    
    async def _background_connection_monitor(self, job_id: str, batch_idx: int):
        """백그라운드 연결 모니터링 (비동기, 논블로킹)"""
        try:
            # 빠른 연결 상태만 확인 (상세 정보 없이)
            has_connections = await notification_service.has_active_connections(job_id)
            
            if not has_connections:
                logger.warning(f"⚠️ 배치 {batch_idx + 1}: 활성 연결 없음 (백그라운드 감지)")
            else:
                # 연결이 있을 때만 간단히 로깅 (선택적)
                logger.debug(f"💓 배치 {batch_idx + 1}: 연결 상태 양호")
                
        except Exception as e:
            # 백그라운드 모니터링 실패해도 메인 작업에 영향 없음
            logger.warning(f"⚠️ 배치 {batch_idx + 1}: 백그라운드 연결 확인 실패 - {str(e)}")

    async def _perform_connection_health_check(self, job_id: str):
        """연결 상태 건강성 확인 (상세 정보 포함)"""
        job = self.jobs[job_id]
        current_time = datetime.now()
        
        # 연결 확인 주기 (10초마다)
        if (current_time - job["last_connection_check"]).seconds < 10:
            return
        
        job["last_connection_check"] = current_time
        job["connection_checks"] += 1
        
        health_info = await notification_service.get_connection_health(job_id)
        
        if health_info:
            logger.info(f"💓 Connection health for job {job_id}: "
                f"WS:{health_info['websocket_count']} "
                f"SSE:{health_info['sse_count']} "
                f"Last HB: {health_info['last_heartbeat_ago']:.1f}s ago")
            
            # 하트비트가 너무 오래 전이면 경고
            if health_info['last_heartbeat_ago'] > 60:
                logger.warning(f"⚠️ Heartbeat is stale for job {job_id}")
        else:
            logger.error(f"❌ No connection health info for job {job_id}")
    
    async def _optimized_batch_delay(self, job_id: str, batch_idx: int):
        """최적화된 배치 간 대기 시간 (성능 개선)"""
        delay_start = datetime.now()
        
        # 429 에러 방지를 위한 최소 대기 시간
        base_delay = 1.0
        
        # 연결 상태 확인 (캐시된 결과 사용으로 성능 향상)
        has_connections = await self._cached_connection_check(job_id)
        
        if has_connections:
            # 연결이 있으면 최소 대기
            await asyncio.sleep(base_delay)
        else:
            await asyncio.sleep(base_delay * 2)
        
        delay_duration = (datetime.now() - delay_start).total_seconds()
        logger.debug(f"⏰ 배치 간 대기 완료: {delay_duration:.3f}초")

    async def _cached_connection_check(self, job_id: str) -> bool:
        """캐시된 연결 상태 확인 (성능 최적화)"""
        # 캐시 시간: 5초 (기존 10초에서 단축)
        if not hasattr(self, '_connection_cache'):
            self._connection_cache = {}
        
        current_time = datetime.now()
        cache_key = job_id
        
        # 캐시된 결과가 있고 5초 이내면 재사용
        if (cache_key in self._connection_cache and 
            (current_time - self._connection_cache[cache_key]['timestamp']).total_seconds() < 5):
            return self._connection_cache[cache_key]['has_connections']
        
        # 캐시가 없거나 만료된 경우 새로 확인
        has_connections = await notification_service.has_active_connections(job_id)
        self._connection_cache[cache_key] = {
            'has_connections': has_connections,
            'timestamp': current_time
        }
        
        return has_connections

    async def _smart_delay_with_connection_check(self, job_id: str, base_delay: float):
        """연결 상태를 확인하면서 지능적으로 대기 (429 에러 방지 포함) - 호환성 유지"""
        # 기존 함수 호환성을 위해 유지하되, 최적화된 로직 사용
        await self._optimized_batch_delay(job_id, 0)
    
    async def _generate_single_file(
        self,
        text: str,
        voice: str,
        file_path: str,
        gender_hint: GenderType,
        task_info: Dict[str, Any],
        job_id: str
    ):
        """단일 파일 생성 (연결 상태 확인 포함)"""

        job = self.jobs[job_id]
        start_time = datetime.now()

        try:
            task_info["status"] = "processing"
            task_info["start_time"] = start_time.isoformat()

            logger.info(f"⏱️ 파일 생성 시작: {task_info['filename']} at {start_time.strftime('%H:%M:%S.%f')[:-3]}")

            # 파일 처리 시작 알림 (연결이 있을 때만)
            if await notification_service.has_active_connections(job_id):
                await notification_service.notify_job_progress(job_id, {
                    "filename": task_info["filename"],
                    "status": "processing",
                    "text": text[:50] + "..." if len(text) > 50 else text,
                    "voice": voice
                })

            # Rich Text 태그 제거
            clean_text = strip_rich_text_tags(text)

            api_start = datetime.now()

            # 설정된 TTS 제공자에 따라 라우팅
            tts_provider = job.get("tts_provider", "gemini")
            success = False
            ncp_url = None
            is_rate_limit = False

            if tts_provider == "murf":
                logger.info(f"🎤 Murf TTS로 생성 중...")
                # Murf로 생성
                language = job.get("language", "en")  # 기본값 en
                success, ncp_url, duration = await self._murf_generate(
                    text=clean_text,
                    voice_id=voice,
                    file_path=file_path,
                    language=language
                )
                # Duration을 task_info에 저장
                if success and duration:
                    task_info["duration"] = duration
            elif tts_provider == "openai":
                logger.info(f"🤖 OpenAI TTS로 생성 중...")
                # OpenAI로 생성
                success, ncp_url = await self.openai_repo.generate_tts(
                    text=clean_text,
                    voice=voice,
                    filename=file_path
                )
            else:  # gemini (기본값)
                logger.info(f"🌟 Gemini TTS로 생성 중...")
                # Gemini로 생성 (기존 로직)
                success, ncp_url, is_rate_limit = await self.gemini_repo.generate_tts(
                    text=clean_text,
                    voice=voice,  # 이미 문자열임
                    filename=file_path,
                    gender_hint=gender_hint
                )

                if not success and is_rate_limit:
                    logger.warning("↩️ Falling back to OpenAI TTS due to Gemini 429")
                    # 요청된 성별 힌트에 맞는 OpenAI 보이스 선택
                    openai_voice = self._select_openai_voice_by_gender(gender_hint)
                    new_filename = self._generate_filename(task_info["text_index"], openai_voice, gender_hint)
                    new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
                    # task_info 업데이트
                    task_info["voice"] = openai_voice
                    task_info["filename"] = new_filename
                    task_info["file_path"] = new_file_path
                    task_info["gender_hint"] = self._get_clean_gender_value(gender_hint)
                    success, ncp_url = await self.openai_repo.generate_tts(
                        text=clean_text,
                        voice=openai_voice,
                        filename=new_file_path
                    )

            api_end = datetime.now()
            api_duration = (api_end - api_start).total_seconds()

            # 첫 번째 파일 생성 시간 특별 추적
            is_first_file = task_info["text_index"] == 1
            if is_first_file:
                logger.info(f"🥇 첫 번째 파일 생성 완료: {api_duration:.3f}초")
                if api_duration > 5.0:
                    logger.warning(f"🐌 첫 번째 파일이 매우 느림: {api_duration:.3f}초 > 5초")
                    logger.warning(f"   • Cold start 또는 API 초기화 지연 가능성")

            # API 응답 시간 분석 (네트워크/서버 부하 감지)
            if api_duration > 3.0:
                logger.warning(f"⚠️ TTS API 지연 감지: {api_duration:.3f}초 > 3초")
                logger.warning(f"   • 파일: {task_info['filename']}")
                logger.warning(f"   • 가능 원인: API 서버 부하 또는 네트워크 지연")
            elif api_duration > 2.0:
                logger.info(f"⏰ TTS API 주의: {api_duration:.3f}초 > 2초")
            else:
                logger.info(f"🌐 TTS API 완료: {api_duration:.3f}초")
            
            if success:
                task_info["status"] = "completed"
                task_info["end_time"] = datetime.now().isoformat()
                task_info["ncp_url"] = ncp_url

                # MP3 파일의 duration 계산 (Murf는 이미 계산됨)
                if tts_provider != "murf":
                    file_path = task_info.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        duration = self._get_mp3_duration(file_path)
                        task_info["duration"] = duration

                        # NCP 업로드 성공 후 로컬 파일 삭제
                        try:
                            os.remove(file_path)
                            logger.info(f"🗑️ 로컬 파일 삭제 완료: {file_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ 로컬 파일 삭제 실패: {file_path} - {str(e)}")
                    else:
                        task_info["duration"] = None
                # Murf는 _murf_generate()에서 이미 duration을 계산하여 task_info에 저장함

                job["completed_files"] += 1
                
                # 파일 완료 알림 (연결이 있을 때만)
                if await notification_service.has_active_connections(job_id):
                    await notification_service.notify_job_progress(job_id, {
                        "filename": task_info["filename"],
                        "status": "completed",
                        # "download_url": f"/api/v1/tts/download/{task_info['filename']}"
                    })
            else:
                task_info["status"] = "failed"
                task_info["end_time"] = datetime.now().isoformat()
                job["failed_files"] += 1
                
                # 파일 실패 알림 (연결이 있을 때만)
                if await notification_service.has_active_connections(job_id):
                    await notification_service.notify_job_progress(job_id, {
                        "filename": task_info["filename"],
                        "status": "failed",
                        "error": "TTS 생성 실패"
                    })
                
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = (
                "429" in error_str or 
                "rate limit" in error_str or 
                "too many requests" in error_str or
                "quota exceeded" in error_str
            )
            
            task_info["status"] = "failed"
            task_info["end_time"] = datetime.now().isoformat()
            task_info["error"] = str(e)
            job["failed_files"] += 1
            
            # 429 에러인 경우 추가 대기 시간 적용
            if is_rate_limit:
                logger.warning(f"⚠️ Rate limit error detected for {task_info['filename']}, applying additional delay...")
                await asyncio.sleep(settings.tts_rate_limit_delay)  # 설정된 대기 시간
            
            # 파일 에러 알림 (연결이 있을 때만)
            if await notification_service.has_active_connections(job_id):
                await notification_service.notify_job_progress(job_id, {
                    "filename": task_info["filename"],
                    "status": "failed",
                    "error": str(e),
                    "is_rate_limit": is_rate_limit
                })
            
            logger.error(f"❌ Single file generation failed: {str(e)}")
    
    async def _notify_job_status_change(self, job_id: str):
        """작업 상태 변경 알림 (연결 상태 확인 포함)"""
        job_status = self.get_job_status(job_id)
        if job_status and await notification_service.has_active_connections(job_id):
            await notification_service.broadcast_job_update(job_id, job_status)
    
    async def _notify_job_completion(self, job_id: str):
        """작업 완료 알림 (연결 상태 확인 포함)"""
        job_status = self.get_job_status(job_id)
        if job_status:
            # 완료 알림은 연결이 없어도 시도 (재연결 시 받을 수 있도록)
            await notification_service.notify_job_completion(job_id, job_status)
    
    def pause_job(self, job_id: str) -> bool:
        """작업 일시 중단"""
        if job_id in self.jobs:
            self.jobs[job_id]["paused"] = True
            logger.info(f"⏸️ Job {job_id} paused")
            return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """작업 재개"""
        if job_id in self.jobs:
            self.jobs[job_id]["paused"] = False
            logger.info(f"▶️ Job {job_id} resumed")
            return True
        return False
    
    def _check_ffprobe_available(self) -> bool:
        """ffprobe 사용 가능 여부 확인 (캐시됨)"""
        if not hasattr(self, '_ffprobe_checked'):
            try:
                result = subprocess.run(['ffprobe', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                self._ffprobe_available = result.returncode == 0
                if self._ffprobe_available:
                    logger.info("✅ ffprobe 사용 가능")
                else:
                    logger.error("❌ ffprobe 사용 불가")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._ffprobe_available = False
                logger.error("❌ ffprobe 설치되지 않음")
            self._ffprobe_checked = True
        return self._ffprobe_available

    def _get_mp3_duration_ffmpeg(self, file_path: str) -> Optional[float]:
        """ffprobe를 사용한 정확한 duration 계산 (우선순위)"""
        if not self._check_ffprobe_available():
            return None
            
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ MP3 파일을 찾을 수 없음: {file_path}")
            return None
            
        try:
            import time
            exec_start = time.time()

            # ffprobe 명령어로 정확한 duration 추출
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries',
                'format=duration', '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=10)

            exec_time = time.time() - exec_start

            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                logger.info(f"🎯 ffprobe duration: {duration:.2f}초")

                return round(duration, 2)
            else:
                stderr_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"⚠️ ffprobe 실행 실패: {stderr_msg} (실행시간: {exec_time:.3f}초)")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"⚠️ ffprobe timeout: {file_path}")
            return None
        except Exception as e:
            logger.error(f"⚠️ ffprobe duration 계산 오류: {str(e)}")
            return None

    def _get_mp3_duration(self, file_path: str) -> Optional[float]:
        """MP3 파일의 재생 시간을 초 단위로 계산 (ffprobe만 사용)"""
        import time

        calc_start = time.time()
        logger.info(f"🔍 Duration 계산 시작: {os.path.basename(file_path)}")

        # ffprobe로 duration 계산
        ffprobe_start = time.time()
        duration = self._get_mp3_duration_ffmpeg(file_path)
        if duration is not None:
            ffprobe_time = time.time() - ffprobe_start
            total_time = time.time() - calc_start
            logger.info(f"⏰ Duration 계산 완료 (ffprobe): {ffprobe_time:.3f}초 (총 {total_time:.3f}초)")
            return duration

        total_time = time.time() - calc_start
        logger.error(f"❌ Duration 계산 실패 (ffprobe 사용 불가): {total_time:.3f}초 소요")
        return None
    
    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """작업 상태 조회 (연결 정보 포함)"""
        
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        progress = 0.0
        if job["total_files"] > 0:
            progress = (job["completed_files"] + job["failed_files"]) / job["total_files"]
        
        # 비동기 함수를 동기적으로 호출할 수 없으므로 기본값 사용
        # 실제로는 API 엔드포인트에서 별도로 연결 상태를 확인해야 함
        
        return JobStatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=progress,
            total_files=job["total_files"],
            completed_files=job["completed_files"],
            failed_files=job["failed_files"],
            files=job["files"]
        )
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """모든 작업 상태 조회"""
        
        result = []
        for job_id, job in self.jobs.items():
            progress = 0.0
            if job["total_files"] > 0:
                progress = (job["completed_files"] + job["failed_files"]) / job["total_files"]
            
            result.append({
                "job_id": job_id,
                "status": job["status"],
                "progress": progress,
                "total_files": job["total_files"],
                "completed_files": job["completed_files"],
                "failed_files": job["failed_files"],
                "start_time": job["start_time"].isoformat(),
                "paused": job.get("paused", False),
                "connection_checks": job.get("connection_checks", 0)
            })
        
        return result