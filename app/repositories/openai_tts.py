import asyncio
import os
import boto3
import random
from typing import Optional, Tuple
from io import BytesIO
from datetime import datetime
from app.core.config import settings
from app.models.voice.tts import GenderType

# TTS 로깅 설정
from app.utils.logger.setup import setup_logger

# mod by LAB (25.08.19) 
# from openai import AsyncOpenAI
import base64, tempfile, wave
from pathlib import Path
from pydub import AudioSegment
from google import genai
from google.genai import types
# mod by LAB (25.08.19) 

# mod by LAB (25.08.19) 
# ffmpeg 경로 지정
# AudioSegment.converter = r"C:\Users\murphy\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"

logger = setup_logger('tts_repository', 'logs/tts')

# mod by LAB (25.08.19)  
def _ensure_bytes(data) -> bytes:
    """Gemini inline_data가 bytes 또는 base64 string일 수 있으므로 항상 bytes로 변환"""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        try:
            return base64.b64decode(data)
        except Exception:
            return data.encode("utf-8", "ignore")
    raise TypeError(f"Unsupported audio payload type: {type(data)}")
# mod by LAB (25.08.19)  

# mod by LAB (25.08.19)
def _pcm_to_mp3_file(
    pcm_bytes: bytes, mp3_path: str, sample_rate: int = 24000, channels: int = 1
):
    """
    Raw 16-bit LE PCM → MP3
    pydub이 PCM raw를 직접 읽지 못하므로 메모리 상에서 임시 WAV 헤더를 붙여 변환
    """
    with BytesIO() as wav_buf:
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        wav_buf.seek(0)
        seg = AudioSegment.from_file(wav_buf, format="wav")
        seg.export(mp3_path, format="mp3")
# mod by LAB (25.08.19) 

class GeminiTTSRepository:
    """OpenAI API와의 통신을 담당하는 Repository"""
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        # mod by LAB (25.08.19) 
        api_key = os.getenv("GEMINI_API_KEY", settings.gemini_api_key)
        self.client = genai.Client(api_key=api_key)
        # mod by LAB (25.08.19) 
        
        # NCP S3 클라이언트 설정 (옵션널)
        self.s3_client = None
        if settings.ncp_access_key and settings.ncp_secret_key:
            try:
                self.s3_client = boto3.client(
                    service_name=settings.naver_service_name,
                    endpoint_url=settings.naver_endpoint_url,
                    aws_access_key_id=settings.ncp_access_key,
                    aws_secret_access_key=settings.ncp_secret_key
                )
                logger.info("✅ NCP S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Warning: Failed to initialize NCP S3 client: {str(e)}")
                self.s3_client = None
        else:
            logger.warning("⚠️ Warning: NCP credentials not configured")
    
    def _get_clean_voice_value(self, voice) -> str:
        """Voice 값에서 실제 문자열 값 추출"""
        if hasattr(voice, 'value'):
            return voice.value
        elif isinstance(voice, str):
            return voice
        else:
            return str(voice)
        
    # mod by LAB (25.08.19)  
    @staticmethod
    def _add_mp3_ext(path: str) -> str:
        return path if path.lower().endswith(".mp3") else f"{path}.mp3"
    # mod by LAB (25.08.19)  
    
    def _generate_ncp_path(self, filename: str) -> str:
        """파일명에서 NCP 경로 생성"""
        # 날짜별 폴더 생성
        date_folder = datetime.now().strftime("%Y%m%d")
        return f"{settings.naver_bucket_tts_folder}/{date_folder}/{filename}"
    
    async def upload_to_ncp(self, file_path: str) -> Optional[str]:
        """파일을 NCP에 업로드하고 URL 반환"""
        if not self.s3_client or not settings.naver_bucket_name:
            return None
            
        try:
            filename = os.path.basename(file_path)
            ncp_path = self._generate_ncp_path(filename)
            
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
            logger.info(f"✅ Successfully uploaded to NCP: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"⚠️ NCP upload failed for {file_path}: {str(e)}")
            return None

    async def _is_rate_limit_error(self, error: Exception) -> bool:
        """429 에러인지 확인"""
        error_str = str(error).lower()
        return (
            "429" in error_str or 
            "rate limit" in error_str or 
            "too many requests" in error_str or
            "quota exceeded" in error_str
        )

    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Exponential backoff을 사용한 재시도 로직"""
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                if await self._is_rate_limit_error(e):
                    # 429 에러인 경우 exponential backoff 적용
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ Rate limit detected (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    # 429가 아닌 다른 에러는 즉시 재시도
                    if attempt < max_retries:
                        logger.warning(f"⚠️ API error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying...")
                        await asyncio.sleep(1.0)
                    else:
                        raise e

    async def generate_tts(
        self, text: str, voice, filename: str, gender_hint: GenderType
    ) -> Tuple[bool, Optional[str], bool]:
        """TTS 생성 → PCM 수신 → MP3 저장 → NCP 업로드 URL 반환 (429 에러 재시도 포함)
        반환값: (success, ncp_url, is_rate_limit)
        """
        
        async def _generate_tts_internal():
            # Voice 값을 실제 문자열로 변환
            clean_voice = self._get_clean_voice_value(voice)

            # 단계별 시간 측정 시작
            from datetime import datetime
            start_time = datetime.now()

            logger.info(f"🎵 Generating TTS (Gemini): voice={clean_voice}, file={filename}")

            # mod by LAB (25.08.19)
            # Gemini API 호출 시간 측정
            api_start = datetime.now()
            resp = await self.client.aio.models.generate_content(
                model=settings.tts_model,  # 예: "gemini-2.5-pro-preview-tts"
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=clean_voice
                            )
                        )
                    ),
                ),
            )
            api_end = datetime.now()
            api_duration = (api_end - api_start).total_seconds()

            logger.info(f"⚡ Gemini API 응답: {api_duration:.3f}초")
            
            if not resp or not resp.candidates:
                logger.error(f"❌ Gemini API returned empty response for voice: {clean_voice}")
                raise ValueError(f"Gemini API returned empty response for voice: {clean_voice}")
            
            candidate = resp.candidates[0]
            
            if not candidate.content:
                logger.error(f"❌ Gemini API returned no content for voice: {clean_voice}")
                raise ValueError(f"Gemini API returned no content for voice: {clean_voice}")
            
            if not candidate.content.parts:
                raise ValueError(f"Gemini API returned no audio parts for voice: {clean_voice}")
            
            part = candidate.content.parts[0]
            if not hasattr(part, 'inline_data') or not part.inline_data:
                raise ValueError(f"Gemini API returned no audio data for voice: {clean_voice}")

            # 오디오 처리 시간 측정
            process_start = datetime.now()
            raw = part.inline_data.data
            pcm_bytes = _ensure_bytes(raw)

            # MP3 저장
            base = filename.rsplit(".", 1)[0] if "." in filename else filename
            mp3_path = self._add_mp3_ext(base)
            _pcm_to_mp3_file(pcm_bytes, mp3_path, sample_rate=24000)
            process_end = datetime.now()
            process_duration = (process_end - process_start).total_seconds()

            logger.info(f"🔄 오디오 처리: {process_duration:.3f}초")
            logger.info(f"✅ Saved MP3: {mp3_path}")
            # mod by LAB (25.08.19)

            # NCP 업로드 시간 측정
            upload_start = datetime.now()
            ncp_url = await self.upload_to_ncp(mp3_path)
            upload_end = datetime.now()
            upload_duration = (upload_end - upload_start).total_seconds()

            total_duration = (upload_end - start_time).total_seconds()

            logger.info(f"☁️ NCP 업로드: {upload_duration:.3f}초")
            logger.info(f"⏰ Gemini TTS 총 시간: {total_duration:.3f}초")

            # 지연 경고 및 분석
            if total_duration > 3.0:
                logger.warning(f"⚠️ Gemini TTS 지연: {total_duration:.3f}초 > 3초")
                if api_duration > 2.0:
                    logger.warning(f"   • Gemini API 지연: {api_duration:.3f}초 (병목)")
                if process_duration > 0.5:
                    logger.warning(f"   • 오디오 처리 지연: {process_duration:.3f}초")
                if upload_duration > 1.0:
                    logger.warning(f"   • NCP 업로드 지연: {upload_duration:.3f}초")

            return True, ncp_url, False

        # "no content" 에러에만 재시도, Rate limit은 OpenAI로 전환
        max_retries = settings.tts_max_retries
        base_delay = settings.tts_base_delay
        
        for attempt in range(max_retries + 1):
            try:
                return await _generate_tts_internal()
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit 에러 체크
                is_rate = (
                    "429" in error_str or "rate limit" in error_str or 
                    "too many requests" in error_str or "quota exceeded" in error_str
                )
                
                # "no content" 에러 체크
                is_no_content = (
                    "no content" in error_str or "empty response" in error_str or
                    "returned no content" in error_str
                )
                
                # Rate limit 에러는 즉시 OpenAI로 전환
                if is_rate:
                    logger.warning(f"⚠️ Rate limit detected, switching to OpenAI TTS: {e}")
                    return False, None, True  # is_rate_limit=True로 반환
                
                # 마지막 시도인 경우 에러 발생
                if attempt == max_retries:
                    logger.error(f"❌ Error generating TTS for {filename} (final attempt): {e}")
                    return False, None, False
                
                # "no content" 에러에만 재시도
                if is_no_content:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ 'No content' error detected (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    # 재시도 불가능한 에러는 즉시 반환
                    logger.error(f"❌ Non-retryable error generating TTS for {filename}: {e}")
                    return False, None, False

    async def test_api_connection(self) -> bool:
        """Gemini API 연결 테스트 (429 에러 재시도 포함)"""
        # mod by LAB (25.08.19)  
        
        async def _test_connection_internal():
            resp = await self.client.aio.models.generate_content(
                model=settings.tts_model,
                contents="테스트",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    ),
                ),
            )
            raw = resp.candidates[0].content.parts[0].inline_data.data
            pcm_bytes = _ensure_bytes(raw)

            tmp_base = str(Path(tempfile.gettempdir()) / "gemini_tts_test")
            tmp_mp3 = f"{tmp_base}.mp3"
            _pcm_to_mp3_file(pcm_bytes, tmp_mp3, sample_rate=24000)
             
            try:
                if os.path.exists(tmp_mp3):
                    os.remove(tmp_mp3)
            except Exception:
                pass
            return True

        try:
            await self._retry_with_backoff(
                _test_connection_internal, 
                max_retries=settings.tts_max_retries - 1, 
                base_delay=settings.tts_base_delay / 2
            )
            return True
        except Exception as e:
            logger.error(f"❌ Gemini API connection test failed after retries: {e}")
            return False
        # mod by LAB (25.08.19)
        

# ---------- OpenAI TTS Repository (fallback) ----------
try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None  # type: ignore


class OpenAITTSRepository:
    """OpenAI TTS (gpt-4o-mini-tts) → MP3 저장, NCP 업로드 옵션"""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key) if AsyncOpenAI else None

        # NCP S3 클라이언트(옵션)
        self.s3_client = None
        if settings.ncp_access_key and settings.ncp_secret_key:
            try:
                self.s3_client = boto3.client(
                    service_name=settings.naver_service_name,
                    endpoint_url=settings.naver_endpoint_url,
                    aws_access_key_id=settings.ncp_access_key,
                    aws_secret_access_key=settings.ncp_secret_key,
                )
                logger.info("✅ NCP S3 client initialized successfully (OpenAI)")
            except Exception as e:
                logger.warning(f"⚠️ Warning: Failed to initialize NCP S3 client (OpenAI): {str(e)}")
        else:
            logger.warning("⚠️ Warning: NCP credentials not configured (OpenAI)")

    @staticmethod
    def _add_mp3_ext(path: str) -> str:
        return path if path.lower().endswith(".mp3") else f"{path}.mp3"

    async def upload_to_ncp(self, file_path: str) -> Optional[str]:
        if not self.s3_client or not settings.naver_bucket_name:
            return None
        try:
            filename = os.path.basename(file_path)
            date_folder = datetime.now().strftime("%Y%m%d")
            ncp_path = f"{settings.naver_bucket_tts_folder}/{date_folder}/{filename}"
            with open(file_path, "rb") as f:
                file_content = f.read()
            self.s3_client.upload_fileobj(
                BytesIO(file_content), settings.naver_bucket_name, ncp_path
            )
            self.s3_client.put_object_acl(
                Bucket=settings.naver_bucket_name, Key=ncp_path, ACL="public-read"
            )
            file_url = f"{settings.naver_bucket_name}/{ncp_path}"
            logger.info(f"✅ Uploaded to NCP (OpenAI): {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"⚠️ NCP upload failed for {file_path} (OpenAI): {str(e)}")
            return None

    async def generate_tts(
        self, text: str, voice: Optional[str], filename: str
    ) -> Tuple[bool, Optional[str]]:
        """OpenAI TTS 생성 → MP3 저장 → NCP 업로드 URL 반환"""
        if not self.client:
            logger.error("❌ OpenAI client not available")
            return False, None

        try:
            base = filename.rsplit(".", 1)[0] if "." in filename else filename
            mp3_path = self._add_mp3_ext(base)

            use_voice = (voice or "echo").lower()
            model = settings.openai_tts_model

            # 단계별 시간 측정 시작
            from datetime import datetime
            start_time = datetime.now()
            
            logger.info(f"🔧 OpenAI TTS 시작: model={model}, voice={use_voice}")
            
            # OpenAI API 호출 시간 측정
            api_start = datetime.now()
            async with self.client.audio.speech.with_streaming_response.create(
                model=model,
                voice=use_voice,
                input=text,
                response_format="mp3",
            ) as response:
                await response.stream_to_file(mp3_path)
            api_end = datetime.now()
            api_duration = (api_end - api_start).total_seconds()

            logger.info(f"⚡ OpenAI API 응답: {api_duration:.3f}초")
            logger.info(f"✅ Saved MP3 (OpenAI): {mp3_path}")
            
            ncp_url = await self.upload_to_ncp(mp3_path)
            upload_end = datetime.now()
            
            total_duration = (upload_end - start_time).total_seconds()
                        
            # 지연 경고
            if total_duration > 3.0:
                logger.warning(f"⚠️ OpenAI TTS 지연: {total_duration:.3f}초 > 3초")
                if api_duration > 2.0:
                    logger.warning(f"   • OpenAI API 지연: {api_duration:.3f}초")
            
            return True, ncp_url
        except Exception as e:
            logger.error(f"❌ Error generating TTS (OpenAI) for {filename}: {str(e)}")
            return False, None