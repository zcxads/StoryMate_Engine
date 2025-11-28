from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.config import settings

# 지원되는 언어 감지 모델 목록 (전역 통일)
SUPPORTED_LANGUAGE_DETECTION_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class LanguageDetectionRequest(BaseModel):
    """언어 감지 요청 모델"""
    texts: str
    
class LanguageDetectionResponse(BaseModel):
    """언어 감지 응답 모델"""
    detected_language: Optional[str] = Field(None, description="Detected language code (e.g., 'ko', 'en', 'ja')")


class SupportedLanguageDetectionModelsResponse(BaseModel):
    """지원되는 언어 감지 모델 응답"""
    supported_models: List[str] = Field(default=SUPPORTED_LANGUAGE_DETECTION_MODELS, description="지원되는 모델 목록")
    default_model: str = Field(default=settings.default_llm_model, description="기본 모델")
    total_count: int = Field(default=len(SUPPORTED_LANGUAGE_DETECTION_MODELS), description="총 모델 수")
