from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Union, Any
from app.models.language.orthography import OrthographyRequest

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_ALL_MODELS = [
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
    model: str = Field(description="Language model to use for processing")
    pages: List[TextInput]

# Legacy OCR request (for backward compatibility)
OCRRequest = OrthographyRequest

# Combined request for the /all endpoint that processes Orthography + Sound + Quiz
class AllRequest(OrthographyRequest):
    model: str = Field(description="Language model to use for processing", default="gemini-2.0-flash")
    quizCount: int = 5
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_ALL_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_ALL_MODELS)}")
        return v

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")
