from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any

from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_ORTHOGRAPHY_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash", 
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class TextInput(BaseModel):
    pageKey: int
    text: str

# Base request for Orthography processing
class OrthographyRequest(BaseModel):
    model: str = Field(description="Language model to use for processing", default=settings.default_llm_model)
    pages: List[TextInput]
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_ORTHOGRAPHY_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_ORTHOGRAPHY_MODELS)}")
        return v

class OrthographyResponse(BaseModel):
    """Orthography 응답 모델 (언어 감지 포함)"""
    llmText: List[Dict[str, Any]] = Field(description="Processed pages with corrections")
    detected_language: Optional[str] = Field(None, description="Detected language code (e.g., 'ko', 'en', 'ja')")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")
