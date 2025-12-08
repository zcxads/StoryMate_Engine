from typing import Optional, Tuple
from datetime import datetime

from app.config import settings
from app.utils.logger.setup import setup_logger
from app.repositories.tts.base import BaseTTSRepository
from app.repositories.tts.utils import add_mp3_ext
from app.repositories.storage.ncp_storage import NCPStorageRepository

from openai import AsyncOpenAI

logger = setup_logger('openai_tts_repository', 'logs/tts')


class OpenAITTSRepository(BaseTTSRepository):
    """OpenAI TTS (gpt-4o-mini-tts) → MP3 저장, NCP 업로드 옵션"""

    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        self.api_key = settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key) if AsyncOpenAI else None

        # NCP Storage Repository 초기화
        self.storage = NCPStorageRepository()

    async def generate_tts(
        self, text: str, voice: Optional[str], filename: str, **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """OpenAI TTS 생성 → MP3 저장 → NCP 업로드 URL 반환"""
        if not self.client:
            logger.error("❌ OpenAI client not available")
            return False, None

        try:
            base = filename.rsplit(".", 1)[0] if "." in filename else filename
            mp3_path = add_mp3_ext(base)

            use_voice = (voice or "echo").lower()
            model = settings.openai_tts_model

            # 단계별 시간 측정 시작
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

            ncp_url = await self.storage.upload_to_ncp(mp3_path)
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
