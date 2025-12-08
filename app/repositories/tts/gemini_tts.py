import asyncio
import os
import random
from typing import Optional, Tuple
from datetime import datetime

from google import genai
from google.genai import types

from app.config import settings
from app.models.voice.tts import GenderType
from app.utils.logger.setup import setup_logger
from app.repositories.tts.base import BaseTTSRepository
from app.repositories.tts.utils import ensure_bytes, pcm_to_mp3_file, add_mp3_ext
from app.repositories.storage.ncp_storage import NCPStorageRepository

logger = setup_logger('gemini_tts_repository', 'logs/tts')


class GeminiTTSRepository(BaseTTSRepository):
    """Gemini TTS API와의 통신을 담당하는 Repository"""

    def __init__(self):
        """Gemini 클라이언트 초기화"""
        api_key = os.getenv("GEMINI_API_KEY", settings.gemini_api_key)
        self.client = genai.Client(api_key=api_key)

        # NCP Storage Repository 초기화
        self.storage = NCPStorageRepository()

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
            start_time = datetime.now()

            logger.info(f"🎵 Generating TTS (Gemini): voice={clean_voice}, file={filename}")

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
            pcm_bytes = ensure_bytes(raw)

            # MP3 저장
            base = filename.rsplit(".", 1)[0] if "." in filename else filename
            mp3_path = add_mp3_ext(base)
            pcm_to_mp3_file(pcm_bytes, mp3_path, sample_rate=24000)
            process_end = datetime.now()
            process_duration = (process_end - process_start).total_seconds()

            logger.info(f"🔄 오디오 처리: {process_duration:.3f}초")
            logger.info(f"✅ Saved MP3: {mp3_path}")

            # NCP 업로드 시간 측정
            upload_start = datetime.now()
            ncp_url = await self.storage.upload_to_ncp(mp3_path)
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
