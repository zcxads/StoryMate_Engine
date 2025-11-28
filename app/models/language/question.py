from pydantic import BaseModel, Field, validator
from typing import List, Optional
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_QUESTION_MODELS = [
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

class QuestionRequest(BaseModel):
    model: str = Field(description="Language model to use for processing", default=settings.llm_advanced_analysis_model)
    pages: List[TextInput]
    problem: int = Field(default=5, description="Number of questions to generate", ge=1, le=10)
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_QUESTION_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_QUESTION_MODELS)}")
        return v

class RecommendedQuestion(BaseModel):
    question: str = Field(description="추천 질문")
    reason: str = Field(description="질문에 대한 상세한 설명 및 조사 방향")
    category: str = Field(description="질문 카테고리 (예: 내용이해, 배경지식, 교훈, 등장인물)")
    search_keywords: List[str] = Field(description="웹 검색에 사용할 추천 키워드")

class QuestionResponse(BaseModel):
    recommended_questions: List[RecommendedQuestion] = Field(description="생성된 추천 질문 목록")
    model_used: str = Field(description="The model that was used for processing")
    page_count: int = Field(description="Number of pages processed")
    execution_time: Optional[str] = Field(description="Time taken to process the request")
    
    model_config = {"protected_namespaces": ()}

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수") 