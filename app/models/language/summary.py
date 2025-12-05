from pydantic import BaseModel, Field, validator
from typing import List, Optional

from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_SUMMARY_MODELS = [
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

class SummaryRequest(BaseModel):
    model: str = Field(description="Language model to use for processing", default=settings.default_llm_model)
    pages: List[TextInput]
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_SUMMARY_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_SUMMARY_MODELS)}")
        return v

class SummaryResponse(BaseModel):
    summary: str = Field(description="Generated summary of the book content")
    model_used: str = Field(description="The model that was used for processing")
    page_count: int = Field(description="Number of pages processed")
    execution_time: Optional[str] = Field(description="Time taken to process the request")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수") 