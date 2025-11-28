import os
import aiohttp
import asyncio
import logging
import boto3
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
from io import BytesIO
import time
import wave
import struct

from app.core.config import settings

logger = logging.getLogger(__name__)

def calculate_optimal_duration(text: str, is_bgm: bool = False) -> int:
    """텍스트 내용에 따라 최적의 오디오 길이를 계산"""
    try:
        if is_bgm:
            # 배경음악: 텍스트 길이에 따라 동적 조정
            text_length = len(text)
            word_count = len(text.split())
            
            # 기본 읽기 시간 계산 (한글: 200자/분, 영어: 200단어/분)
            if any('가' <= char <= '힣' for char in text):  # 한글 포함
                reading_time = text_length / 200 * 60  # 초 단위
            else:
                reading_time = word_count / 200 * 60  # 초 단위
            
            # ElevenLabs API 최대 22초 제한 - 배경음악은 최대한 길게
            calculated_duration = max(18, min(22, int(reading_time * 1.5)))
            optimal_duration = 22  # ElevenLabs 최대값인 22초로 고정
            logger.info(f"🎵 배경음악 최적 길이: {optimal_duration}초 (text_length: {text_length}, reading_time: {reading_time:.1f}s, calculated: {calculated_duration})")
            return optimal_duration
        else:
            # 효과음: ElevenLabs 최대 22초 제한 고려 + 내용에 따라 조정
            text_lower = text.lower()
            
            # 지속적인 소리 (배경 소음, 환경 소음)
            continuous_sounds = ['rain', 'wind', 'ocean', 'river', 'fire', 'forest', 'water', 'stream', 
                               '비', '바람', '바다', '강', '불', '숲', '물', '개울']
            if any(sound in text_lower for sound in continuous_sounds):
                return 4  # 4초로 요청 (API 제한 내에서 적절한 길이)
            
            # 순간적인 액션 소리 - 짧게 요청
            action_sounds = ['knock', 'click', 'pop', 'bang', 'crash', 'door', 'step', 'footstep',
                           '노크', '클릭', '충돌', '방문', '발소리', '문']
            if any(sound in text_lower for sound in action_sounds):
                return 2  # 2초로 요청
            
            # 일반적인 효과음
            return 3  # 3초로 요청
            
    except Exception as e:
        logger.warning(f"최적 길이 계산 실패: {str(e)}")
        return 20 if is_bgm else 3

def create_professional_sound_prompt(description: str, additional_info: dict = None) -> str:
    """전문적인 사운드 프롬프트 생성 (ElevenLabs 2024 모범 사례 기반)"""
    try:
        # 기본 효과음 타입 분류
        description_lower = description.lower()
        
        # 더 구체적인 Foley 사운드 카테고리 분류
        if any(word in description_lower for word in ['step', 'walk', 'footstep', '발소리', '걸음', 'walking']):
            category = "footstep foley sound"
            quality_desc = "crisp, realistic footsteps on various surfaces"
            technical_desc = "recorded with professional microphones"
        elif any(word in description_lower for word in ['door', 'knock', 'bang', '문', '노크', 'knocking']):
            category = "impact foley sound"
            quality_desc = "sharp, resonant knocking or door sound"
            technical_desc = "clear transient response"
        elif any(word in description_lower for word in ['water', 'rain', 'river', '물', '비', '강', 'flowing', 'splash']):
            category = "water ambient sound"
            quality_desc = "natural, flowing water with rich harmonics"
            technical_desc = "stereo field recording"
        elif any(word in description_lower for word in ['wind', 'breeze', '바람', 'windy']):
            category = "wind ambient sound"
            quality_desc = "gentle, atmospheric wind movement"
            technical_desc = "natural outdoor recording"
        elif any(word in description_lower for word in ['animal', 'bird', '동물', '새', 'chirping', 'singing']):
            category = "nature animal sound"
            quality_desc = "authentic, clear animal vocalization"
            technical_desc = "wildlife field recording"
        elif any(word in description_lower for word in ['laugh', 'giggle', '웃음', 'laughter']):
            category = "human vocal sound"
            quality_desc = "natural, joyful laughter"
            technical_desc = "studio recorded vocal"
        elif any(word in description_lower for word in ['bell', 'chime', '종', 'ring']):
            category = "metallic resonance sound"
            quality_desc = "clear, sustained bell tone"
            technical_desc = "high-frequency detail preserved"
        else:
            category = "foley sound effect"
            quality_desc = "clear, distinct audio"
            technical_desc = "professionally recorded"
        
        # 기본 프롬프트 구성 (더 전문적)
        base_prompt = f"High-quality {category}, {quality_desc}, {technical_desc}, {description}"
        
        # 추가 정보가 있으면 프롬프트에 포함
        if additional_info:
            context_parts = []
            
            situation = additional_info.get('situation', '')
            environment = additional_info.get('environment', '')
            action = additional_info.get('action', '')
            affect = additional_info.get('affect', '')
            
            if environment and environment != 'None':
                context_parts.append(f"recorded in {environment} setting")
            if situation and situation != 'None':
                context_parts.append(f"capturing {situation} scenario")
            if action and action != 'None':
                context_parts.append(f"emphasizing {action} movement")
            if affect and affect != 'None':
                context_parts.append(f"conveying {affect} atmosphere")
            
            if context_parts:
                base_prompt += f", {', '.join(context_parts)}"
        
        # 오디오 품질 및 기술적 사양 강조
        final_prompt = f"{base_prompt}, studio-grade audio quality, no background noise, clean recording, full frequency range, professional sound design, sustained sound throughout full duration"
        
        logger.info(f"🎧 생성된 전문 프롬프트: {final_prompt[:150]}...")
        return final_prompt
        
    except Exception as e:
        logger.error(f"프롬프트 생성 실패: {str(e)}")
        return f"High-quality foley sound effect, professionally recorded, {description}, studio-grade audio quality"

def parse_mp3_header(audio_data: bytes) -> float:
    """MP3 헤더를 직접 파싱하여 오디오 길이 계산"""
    try:
        # MP3 프레임 헤더 비트레이트 테이블 (MPEG-1 Layer 3)
        bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
        sample_rates = [44100, 48000, 32000, 0]
        
        # MP3 헤더 찾기 (0xFF, 0xFB 또는 0xFF, 0xFA)
        for i in range(len(audio_data) - 4):
            if audio_data[i] == 0xFF and (audio_data[i + 1] & 0xE0) == 0xE0:
                # 헤더 발견
                header = struct.unpack('>I', audio_data[i:i+4])[0]
                
                # 비트레이트와 샘플레이트 추출
                bitrate_index = (header >> 12) & 0x0F
                sample_rate_index = (header >> 10) & 0x03
                
                if bitrate_index < len(bitrates) and sample_rate_index < len(sample_rates):
                    bitrate = bitrates[bitrate_index] * 1000  # kbps to bps
                    sample_rate = sample_rates[sample_rate_index]
                    
                    if bitrate > 0 and sample_rate > 0:
                        # 파일 크기 기반 길이 계산
                        duration = (len(audio_data) * 8) / bitrate
                        return duration
        
        return 0.0
    except Exception as e:
        logger.warning(f"MP3 헤더 파싱 실패: {str(e)}")
        return 0.0

def get_audio_duration(audio_data: bytes, is_bgm: bool = False) -> float:
    """오디오 데이터의 실제 길이를 초 단위로 반환"""
    try:
        if len(audio_data) > 0:
            # MP3 헤더 직접 파싱 시도
            parsed_duration = parse_mp3_header(audio_data)
            if parsed_duration > 0:
                logger.info(f"🎵 MP3 헤더 파싱으로 측정된 길이: {parsed_duration:.2f}초")
                return parsed_duration
            
            # 헤더 파싱 실패시 개선된 추정 방식 사용
            file_size_bytes = len(audio_data)
            file_size_kb = file_size_bytes / 1024
            
            logger.info(f"🎵 오디오 파일 정보: {file_size_bytes} bytes ({file_size_kb:.1f} KB)")
            
            # ElevenLabs API는 일반적으로 128kbps MP3를 사용
            # 더 정확한 추정을 위해 여러 비트레이트로 계산
            estimates = []
            
            # 64kbps = 8KB/sec
            estimates.append(("64kbps", file_size_kb / 8.0))
            # 96kbps = 12KB/sec  
            estimates.append(("96kbps", file_size_kb / 12.0))
            # 128kbps = 16KB/sec (가장 일반적)
            estimates.append(("128kbps", file_size_kb / 16.0))
            # 192kbps = 24KB/sec
            estimates.append(("192kbps", file_size_kb / 24.0))
            
            for rate, duration in estimates:
                logger.info(f"🎵 {rate} 기준 추정 길이: {duration:.2f}초")
            
            # ElevenLabs API는 일반적으로 128kbps를 사용하므로 이를 기준으로 함
            estimated_duration = file_size_kb / 16.0
            
            # 너무 짧은 경우 다른 비트레이트 시도
            if estimated_duration < 1.0:
                # 64kbps 기준으로 재계산
                estimated_duration = file_size_kb / 8.0
                logger.info(f"🎵 64kbps 기준으로 재계산: {estimated_duration:.2f}초")
            
            logger.info(f"🎵 최종 추정 길이: {estimated_duration:.2f}초")
            
            # ElevenLabs API 제한사항 반영 (최대 22초)
            if is_bgm:
                return max(min(estimated_duration, 22.0), 1.0)  # 1-22초 범위
            else:
                return max(min(estimated_duration, 22.0), 0.5)  # 0.5-22초 범위
        
        return 20.0 if is_bgm else 3.0  # 기본값도 API 제한에 맞춤
    except Exception as e:
        logger.warning(f"오디오 길이 측정 실패: {str(e)}")
        return 20.0 if is_bgm else 3.0

class SoundGeneratorRepository:
    """SOUND 전용 음악/효과음 생성 Repository (ElevenLabs API 사용)"""
    
    def __init__(self):
        self.elevenlabs_api_key = os.getenv('ELEVENLABS')
        
        # NCP S3 클라이언트 설정
        self.s3_client = None
        if settings.ncp_access_key and settings.ncp_secret_key:
            try:
                self.s3_client = boto3.client(
                    service_name=settings.naver_service_name,
                    endpoint_url=settings.naver_endpoint_url,
                    aws_access_key_id=settings.ncp_access_key,
                    aws_secret_access_key=settings.ncp_secret_key
                )
                logger.info("✅ NCP S3 client initialized successfully for Sound Generator")
            except Exception as e:
                logger.error(f"⚠️ Failed to initialize NCP S3 client: {str(e)}")
                self.s3_client = None
        else:
            logger.warning("⚠️ NCP credentials not configured")
        
    def _generate_ncp_path(self, filename: str, is_bgm: bool = True) -> str:
        """파일명에서 NCP 경로 생성 (BGM/Effect 폴더 사용)"""
        # 날짜별 폴더 생성
        date_folder = datetime.now().strftime("%Y%m%d")
        
        if is_bgm:
            # 배경음악은 BGM 폴더 사용
            bucket_folder = settings.naver_bucket_bgm_folder
        else:
            # 효과음은 Effect 폴더 사용
            bucket_folder = settings.naver_bucket_effect_folder
            
        return f"{bucket_folder}/{date_folder}/{filename}"
        
    async def generate_background_music(self, description: str, filename: str, text_content: str = "") -> Tuple[bool, str, float]:
        """배경음악 생성 (ElevenLabs API 사용) - 오디오 길이도 반환"""
        start_time = time.time()
        try:
            logger.info(f"🎵 배경음악 생성 시작: {description}")
            
            # ElevenLabs API 키 확인
            logger.info(f"🔑 ElevenLabs API 키 상태: {'설정됨' if self.elevenlabs_api_key else '설정되지 않음'}")
            if not self.elevenlabs_api_key:
                logger.error("❌ ElevenLabs API 키가 설정되지 않았습니다")
                return False, "", 0.0
            
            # 텍스트 내용에 따라 최적 길이 계산
            optimal_duration = calculate_optimal_duration(text_content or description, is_bgm=True)
            
            # 배경음악임을 명시적으로 강조하는 프롬프트 생성
            bgm_instruction = f"Create a continuous {optimal_duration}-second ambient background music. "
            base_description = description[:380] if len(description) > 380 else description  # 지시문을 위한 공간 확보
            bgm_prompt = f"{bgm_instruction}Looping atmospheric music based on: {base_description}"
            
            if len(bgm_prompt) > 450:
                # 450자 제한 처리
                available_space = 450 - len(bgm_instruction) - len("Looping atmospheric music based on: ")
                base_description = description[:available_space]
                bgm_prompt = f"{bgm_instruction}Looping atmospheric music based on: {base_description}"
            
            logger.info(f"🎵 최종 배경음악 프롬프트: {bgm_prompt}")
            logger.info(f"🎵 요청 길이: {optimal_duration}초, 프롬프트 영향력: 0.9")
            
            # ElevenLabs Music Generation API 요청 (배경음악 전용 엔드포인트)
            async with aiohttp.ClientSession() as session:
                url = "https://api.elevenlabs.io/v1/sound-generation"  # 현재로서는 같은 엔드포인트, 하지만 파라미터로 구분 시도
                
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_api_key
                }
                
                json = {
                    "text": bgm_prompt,
                    "duration_seconds": optimal_duration,  # 올바른 파라미터명 사용
                    "prompt_influence": 0.9  # 배경음악 텍스트를 강하게 반영
                }
                
                # 재시도 로직 추가 (429 에러 대응)
                max_retries = 3
                retry_delay = 2  # 초기 대기 시간 (초)
                
                for attempt in range(max_retries):
                    try:
                        async with session.post(url, headers=headers, json=json) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                logger.info(f"🎵 ElevenLabs Sound Generation 응답 성공")
                                
                                # 실제 오디오 길이 측정
                                audio_duration = get_audio_duration(audio_data, is_bgm=True)
                                logger.info(f"🎵 실제 배경음악 길이: {audio_duration:.2f}초 (요청: {optimal_duration}초)")
                                
                                # 직접 NCP 업로드 (임시 파일 없이)
                                ncp_url = await self._upload_audio_data_to_ncp(audio_data, filename, is_bgm=True)
                                
                                if ncp_url:
                                    execution_time = time.time() - start_time
                                    logger.info(f"✅ 배경음악 생성 완료: {ncp_url} (처리 시간: {execution_time:.2f}초)")
                                    return True, ncp_url, audio_duration
                                else:
                                    execution_time = time.time() - start_time
                                    logger.error(f"❌ NCP 업로드 실패 (처리 시간: {execution_time:.2f}초)")
                                    return False, "", 0.0
                            elif response.status == 429:
                                error_text = await response.text()
                                logger.warning(f"⚠️ ElevenLabs API 과부하 (429): 시도 {attempt + 1}/{max_retries}")
                                logger.warning(f"⚠️ 대기 시간: {retry_delay}초 후 재시도")
                                
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                    retry_delay *= 2  # 지수 백오프
                                    continue
                                else:
                                    execution_time = time.time() - start_time
                                    logger.error(f"❌ ElevenLabs API 과부하로 인한 최종 실패: {error_text} (처리 시간: {execution_time:.2f}초)")
                                    return False, "", 0.0
                            else:
                                error_text = await response.text()
                                execution_time = time.time() - start_time
                                logger.error(f"❌ ElevenLabs Sound Generation 생성 실패: HTTP {response.status} - {error_text} (처리 시간: {execution_time:.2f}초)")
                                return False, "", 0.0
                                
                    except aiohttp.ClientError as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ ElevenLabs API 연결 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            execution_time = time.time() - start_time
                            logger.error(f"❌ ElevenLabs Sound Generation 연결 오류 (최종): {str(e)} (처리 시간: {execution_time:.2f}초)")
                            return False, "", 0.0
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 배경음악 생성 실패: {str(e)} (처리 시간: {execution_time:.2f}초)")
            import traceback
            logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
            return False, "", 0.0
    
    async def generate_sound_effect(self, description: str, filename: str, additional_info: dict = None, original_text: str = "") -> Tuple[bool, str, float]:
        """효과음 생성 (ElevenLabs HTTP 요청 - 벡터 DB sentence 기반) - 오디오 길이도 반환"""
        start_time = time.time()
        try:
            logger.info(f"🔊 효과음 생성 시작: {description}")
            
            # ElevenLabs API 키 확인
            logger.info(f"🔑 ElevenLabs API 키 상태: {'설정됨' if self.elevenlabs_api_key else '설정되지 않음'}")
            if not self.elevenlabs_api_key:
                logger.error("❌ ElevenLabs API 키가 설정되지 않았습니다")
                return False, "", 0.0
            
            # 텍스트 내용에 따라 최적 길이 계산
            optimal_duration = calculate_optimal_duration(original_text or description, is_bgm=False)
            
            # 벡터 DB에서 검색된 원본 문장만 사용
            effect_prompt = description[:450] if len(description) > 450 else description
            
            logger.info(f"🔊 최종 효과음 프롬프트: {effect_prompt}")
            logger.info(f"🔊 요청 길이: {optimal_duration}초, 프롬프트 영향력: 0.9")
            
            # ElevenLabs Sound Generation API 요청 (HTTP 방식)
            async with aiohttp.ClientSession() as session:
                url = "https://api.elevenlabs.io/v1/sound-generation"
                
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_api_key
                }
                
                json = {
                    "text": effect_prompt,
                    "duration_seconds": optimal_duration,  # 올바른 파라미터명 사용
                    "prompt_influence": 0.7  # 효과음은 0.7로 설정
                }
                
                # 재시도 로직 추가 (429 에러 대응)
                max_retries = 3
                retry_delay = 2  # 초기 대기 시간 (초)
                
                for attempt in range(max_retries):
                    try:
                        async with session.post(url, headers=headers, json=json) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                logger.info(f"🔊 ElevenLabs Sound Generation 응답 성공")
                                
                                # 오디오 길이 측정
                                audio_duration = get_audio_duration(audio_data, is_bgm=False)
                                logger.info(f"🔊 측정된 효과음 길이: {audio_duration:.2f}초 (요청: {optimal_duration}초)")
                                
                                # 직접 NCP 업로드 (임시 파일 없이)
                                ncp_url = await self._upload_audio_data_to_ncp(audio_data, filename, is_bgm=False)
                                
                                if ncp_url:
                                    execution_time = time.time() - start_time
                                    logger.info(f"✅ 효과음 생성 완료: {ncp_url} (처리 시간: {execution_time:.2f}초, 길이: {audio_duration:.2f}초)")
                                    return True, ncp_url, audio_duration
                                else:
                                    execution_time = time.time() - start_time
                                    logger.error(f"❌ NCP 업로드 실패 (처리 시간: {execution_time:.2f}초)")
                                    return False, "", 0.0
                            elif response.status == 429:
                                error_text = await response.text()
                                logger.warning(f"⚠️ ElevenLabs API 과부하 (429): 시도 {attempt + 1}/{max_retries}")
                                logger.warning(f"⚠️ 대기 시간: {retry_delay}초 후 재시도")
                                
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                    retry_delay *= 2  # 지수 백오프
                                    continue
                                else:
                                    execution_time = time.time() - start_time
                                    logger.error(f"❌ ElevenLabs API 과부하로 인한 최종 실패: {error_text} (처리 시간: {execution_time:.2f}초)")
                                    return False, "", 0.0
                            else:
                                error_text = await response.text()
                                execution_time = time.time() - start_time
                                logger.error(f"❌ ElevenLabs Sound Generation 생성 실패: HTTP {response.status} - {error_text} (처리 시간: {execution_time:.2f}초)")
                                return False, "", 0.0
                                
                    except aiohttp.ClientError as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ ElevenLabs API 연결 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            execution_time = time.time() - start_time
                            logger.error(f"❌ ElevenLabs Sound Generation 연결 오류 (최종): {str(e)} (처리 시간: {execution_time:.2f}초)")
                            return False, "", 0.0
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 효과음 생성 실패: {str(e)} (처리 시간: {execution_time:.2f}초)")
            logger.error(f"❌ 사용된 프롬프트: {effect_prompt if 'effect_prompt' in locals() else 'N/A'}")
            import traceback
            logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
            return False, "", 0.0
    
    async def _download_and_upload_to_ncp(self, audio_url: str, filename: str, is_bgm: bool = True) -> str:
        """오디오 파일 다운로드 및 로컬 저장 + NCP 업로드"""
        start_time = time.time()
        try:
            logger.info(f"📥 파일 다운로드 시작: {audio_url}")
            
            # 파일 다운로드
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as response:
                        response.raise_for_status()
                        audio_data = await response.read()
                        
                        if len(audio_data) == 0:
                            logger.error("❌ 다운로드된 오디오 데이터가 비어있습니다")
                            return ""
                        
            except Exception as e:
                logger.error(f"❌ 파일 다운로드 실패: {str(e)}")
                return ""
            
            # sound_output 폴더에 로컬 저장
            sound_output_dir = settings.sound_output_dir
            
            # 절대 경로로 변환
            if not os.path.isabs(sound_output_dir):
                sound_output_dir = os.path.abspath(sound_output_dir)
                logger.info(f"📁 절대 경로로 변환: {sound_output_dir}")
            
            try:
                os.makedirs(sound_output_dir, exist_ok=True)
                logger.info(f"📁 디렉토리 생성/확인 완료: {sound_output_dir}")
            except Exception as e:
                logger.error(f"❌ 디렉토리 생성 실패: {str(e)}")
                logger.error(f"❌ 현재 작업 디렉토리: {os.getcwd()}")
                logger.error(f"❌ 상대 경로: {settings.sound_output_dir}")
                return ""
            
            # filename이 이미 전체 경로를 포함하고 있는지 확인
            if os.path.dirname(filename):
                # 이미 경로가 포함되어 있으면 파일명만 추출
                local_filename = os.path.basename(filename)
            else:
                # 파일명만 있는 경우
                local_filename = filename
            
            # 파일명에 타임스탬프 추가 (중복 방지)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(local_filename)
            local_filename = f"{base_name}_{timestamp}{ext}"
            
            file_path = os.path.join(sound_output_dir, local_filename)
            
            # 파일 저장 시도
            try:
                with open(file_path, 'wb') as f:
                    f.write(audio_data)
                
            except Exception as e:
                logger.error(f"❌ 파일 쓰기 실패: {str(e)}")
                logger.error(f"❌ 파일 경로: {file_path}")
                return ""
            
            # NCP 업로드 (BGM/Effect 폴더 사용)
            if self.s3_client and settings.naver_bucket_name:
                try:
                    ncp_path = self._generate_ncp_path(local_filename, is_bgm=is_bgm)
                    logger.info(f"📤 NCP 업로드 경로: {ncp_path}")
                    
                    # 파일을 바이트로 읽기
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    file_obj = BytesIO(file_content)
                    
                    # NCP에 파일 업로드
                    self.s3_client.upload_fileobj(
                        file_obj, 
                        settings.naver_bucket_name, 
                        ncp_path
                    )
                    
                    # 파일을 공개로 설정
                    self.s3_client.put_object_acl(
                        Bucket=settings.naver_bucket_name, 
                        Key=ncp_path, 
                        ACL='public-read'
                    )
                    
                    # URL 생성 및 반환
                    file_url = f"{settings.naver_bucket_name}/{ncp_path}"
                    execution_time = time.time() - start_time
                    logger.info(f"✅ Successfully uploaded to NCP: {file_url} (업로드 시간: {execution_time:.2f}초)")
                    return file_url
                    
                except Exception as e:
                    logger.error(f"⚠️ NCP upload failed for {file_path}: {str(e)}")
                    # NCP 업로드 실패해도 로컬 파일은 유지
                    logger.info(f"💾 로컬 파일은 유지됨: {file_path}")
                    return ""
            else:
                logger.warning("NCP S3 client not available, 로컬 파일만 저장됨")
                logger.info(f"💾 로컬 파일 저장: {file_path}")
                return ""
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"파일 다운로드 및 업로드 실패: {str(e)} (처리 시간: {execution_time:.2f}초)")
            import traceback
            logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
            return ""
    
    async def _upload_audio_data_to_ncp(self, audio_data: bytes, filename: str, is_bgm: bool = True) -> str:
        """오디오 데이터를 직접 NCP S3에 업로드"""
        start_time = time.time()
        try:
            logger.info(f"📤 오디오 데이터 직접 NCP 업로드 시작")
            
            if not self.s3_client or not settings.naver_bucket_name:
                logger.error("❌ NCP S3 클라이언트가 설정되지 않았습니다")
                return ""
            
            # NCP 경로 생성
            ncp_path = self._generate_ncp_path(filename, is_bgm)
            logger.info(f"📤 NCP 업로드 경로: {ncp_path}")
            
            # BytesIO 객체로 변환
            file_obj = BytesIO(audio_data)
            
            # NCP에 파일 업로드
            self.s3_client.upload_fileobj(
                file_obj, 
                settings.naver_bucket_name, 
                ncp_path
            )
            
            # 파일을 공개로 설정
            self.s3_client.put_object_acl(
                Bucket=settings.naver_bucket_name, 
                Key=ncp_path, 
                ACL='public-read'
            )
            
            # URL 생성 및 반환
            file_url = f"{settings.naver_bucket_name}/{ncp_path}"
            execution_time = time.time() - start_time
            logger.info(f"✅ 오디오 데이터 직접 NCP 업로드 완료: {file_url} (처리 시간: {execution_time:.2f}초)")
            return file_url
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 오디오 데이터 직접 NCP 업로드 실패: {str(e)} (처리 시간: {execution_time:.2f}초)")
            return ""
    
    async def _upload_local_file_to_ncp(self, file_path: str, filename: str, is_bgm: bool = True) -> str:
        """로컬 파일을 NCP S3에 업로드"""
        start_time = time.time()
        try:
            logger.info(f"📤 로컬 파일 NCP 업로드 시작: {file_path}")
            
            if not self.s3_client or not settings.naver_bucket_name:
                logger.error("❌ NCP S3 클라이언트가 설정되지 않았습니다")
                return ""
            
            # NCP 경로 생성
            ncp_path = self._generate_ncp_path(filename, is_bgm)
            logger.info(f"📤 NCP 업로드 경로: {ncp_path}")
            
            # 파일을 바이트로 읽기
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            file_obj = BytesIO(file_content)
            
            # NCP에 파일 업로드
            self.s3_client.upload_fileobj(
                file_obj, 
                settings.naver_bucket_name, 
                ncp_path
            )
            
            # 파일을 공개로 설정
            self.s3_client.put_object_acl(
                Bucket=settings.naver_bucket_name, 
                Key=ncp_path, 
                ACL='public-read'
            )
            
            # URL 생성 및 반환
            file_url = f"{settings.naver_bucket_name}/{ncp_path}"
            execution_time = time.time() - start_time
            logger.info(f"✅ 로컬 파일 NCP 업로드 완료: {file_url} (처리 시간: {execution_time:.2f}초)")
            return file_url
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 로컬 파일 NCP 업로드 실패: {str(e)} (처리 시간: {execution_time:.2f}초)")
            return ""
