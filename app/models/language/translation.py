from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_TRANSLATION_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash", 
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class TranslationRequest(BaseModel):
    """번역 요청 모델"""
    model: str = Field(description="Language model to use for processing", default=settings.default_llm_model)
    llmText: List[Dict[str, Any]]
    target: str = Field(description="Target language code (default: Korean)", default=settings.language_code[0])
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_TRANSLATION_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_TRANSLATION_MODELS)}")
        return v

class TranslationResponse(BaseModel):
    """번역 응답 모델"""
    state: str = Field(description="Success or failure status")
    llmText: List[Dict[str, Any]] = Field(description="Translated text data with the same structure as the input")
    target: str = Field(description="Target language code that was used for translation")
    error: Optional[str] = Field(None, description="Error message if translation failed")
    execution_time: Optional[str] = Field(None, description="API execution time")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")
