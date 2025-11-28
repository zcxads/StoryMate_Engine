from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_SOUND_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash", 
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class SoundRequest(BaseModel):
    """사운드 및 배경음악 생성 요청 모델"""
    model: str = Field(description="Language model to use for processing", default="gemini-2.0-flash")
    llmText: List[Dict[str, Any]]
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_SOUND_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_SOUND_MODELS)}")
        return v

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")
