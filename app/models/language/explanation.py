from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from app.models.language.content_category import Genre
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_EXPLANATION_MODELS = [
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class ExplanationRequest(BaseModel):
    model: str = Field(description="Language model to use for processing", default=settings.llm_for_explanation)
    problem: str = Field(description="Base64 encoded image of the problem")
    language: str = Field(description="Response language (ko, en, ja, zh)", default=settings.language_code[0])
    force_model: Optional[bool] = Field(default=False, description="강제로 지정한 모델만 사용하고 fallback 모델을 사용하지 않음")
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_EXPLANATION_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_EXPLANATION_MODELS)}")
        return v
    
    @validator('language')
    def validate_language(cls, v):
        if v not in settings.language_code:
            raise ValueError(f"지원되지 않는 언어입니다. 지원 언어: {', '.join(settings.language_code)}")
        return v
    
    model_config = {"protected_namespaces": ()}

class DebugInfo(BaseModel):
    requested_model: str = Field(description="사용자가 요청한 원본 모델")
    fallback_used: bool = Field(description="fallback 모델 사용 여부")
    model_chain: List[str] = Field(description="모델 처리 체인")
    
    model_config = {"protected_namespaces": ()}

class ExplanationResponse(BaseModel):
    answer: str = Field(description="The answer to the problem")
    solution: str = Field(description="Detailed solution process of the problem")
    concepts: str = Field(description="Key concepts related to the problem")
    genre: Optional[Genre] = Field(default=None, description="콘텐츠 장르")
    model_used: str = Field(description="The model that was used for processing")
    execution_time: Optional[str] = Field(description="Time taken to process the request")
    status: Optional[str] = Field(description="Processing status")

    model_config = {"protected_namespaces": ()}

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")


class SimilarQuizRequest(BaseModel):
    """유사 문제 생성 요청 모델 (이미지 기반)"""
    model: str = Field(description="Language model to use for processing", default=settings.default_llm_model)
    problem: str = Field(description="Base64 encoded image of the problem")
    language: str = Field(description="Response language (ko, en, ja, zh)", default=settings.language_code[0])
    force_model: Optional[bool] = Field(default=False, description="강제로 지정한 모델만 사용하고 fallback 모델을 사용하지 않음")

    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_EXPLANATION_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_EXPLANATION_MODELS)}")
        return v

    @validator('language')
    def validate_language(cls, v):
        if v not in settings.language_code:
            raise ValueError(f"지원되지 않는 언어입니다. 지원 언어: {', '.join(settings.language_code)}")
        return v

    model_config = {"protected_namespaces": ()}


class SimilarQuizResponse(BaseModel):
    """유사 문제 생성 응답 모델"""
    question: str = Field(description="생성된 유사 문제")
    answer: str = Field(description="정답")
    options: List[str] = Field(description="선택지 목록 (객관식인 경우), 주관식인 경우 빈 리스트")
    explanation: str = Field(description="문제 해설")
    execution_time: Optional[str] = Field(None, description="API execution time") 