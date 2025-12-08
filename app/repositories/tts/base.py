from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BaseTTSRepository(ABC):
    """TTS Repository의 추상 베이스 클래스"""

    @abstractmethod
    async def generate_tts(self, text: str, voice, filename: str, **kwargs) -> Tuple[bool, Optional[str], ...]:
        """TTS 생성 및 파일 저장

        Args:
            text: 변환할 텍스트
            voice: 음성 설정
            filename: 저장할 파일명
            **kwargs: 추가 파라미터

        Returns:
            (성공 여부, NCP URL, 추가 상태...)
        """
        pass

    def _get_clean_voice_value(self, voice) -> str:
        """Voice 값에서 실제 문자열 값 추출"""
        if hasattr(voice, 'value'):
            return voice.value
        elif isinstance(voice, str):
            return voice
        else:
            return str(voice)
