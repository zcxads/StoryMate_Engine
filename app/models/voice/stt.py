from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from app.core.config import settings

class SupportedSTTLanguage(str, Enum):
    """지원되는 STT 언어 목록"""
    AUTO = "auto"  # 자동 감지
    KO = "ko"      # 한국어
    EN = "en"      # 영어
    JA = "ja"      # 일본어
    ZH = "zh"      # 중국어

class STTRequest(BaseModel):
    """STT 요청 모델"""
    text: str = Field(description="STT로 변환된 텍스트")

class STTResponse(BaseModel):
    """STT 응답 모델 (기능 매칭 결과만 반환)"""
    matched: bool = Field(description="기능 매칭 성공 여부")
    component: Optional[str] = Field(None, description="매칭된 기능 이름")
    score: float = Field(description="유사도 점수 (0.0-1.0)")
    reason: str = Field(description="매칭 결과 설명")
    message: Optional[str] = Field(None, description="사용자 메시지")

class STTErrorResponse(BaseModel):
    """STT 에러 응답 모델"""
    message: str = Field(description="에러 메시지")


# 지원되는 오디오 형식
SUPPORTED_AUDIO_FORMATS = [
    'flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm'
]

# 지원되는 STT 모델 목록
SUPPORTED_STT_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini",
]

class SupportedSTTModelsResponse(BaseModel):
    """지원되는 STT 모델 응답"""
    supported_models: List[str] = Field(default=SUPPORTED_STT_MODELS, description="지원되는 모델 목록")
    default_model: str = Field(default=settings.default_llm_model, description="기본 모델")
    total_count: int = Field(default=len(SUPPORTED_STT_MODELS), description="총 모델 수")