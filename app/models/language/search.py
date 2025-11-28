from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from pydantic import validator
from app.models.language.content_category import Genre
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_SEARCH_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class SearchRequest(BaseModel):
    question: str = Field(description="검색할 질문")
    search_keywords: List[str] = Field(description="검색 키워드 목록")
    model: str = Field(description="사용할 AI 모델", default=settings.llm_text_processing_model)
    max_results: int = Field(description="최대 검색 결과 수", default=5, ge=1, le=10)
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_SEARCH_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_SEARCH_MODELS)}")
        return v

    model_config = {"protected_namespaces": ()}

class SearchResult(BaseModel):
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    snippet: str = Field(description="Brief description or excerpt from the result")
    relevance_score: Optional[float] = Field(description="Relevance score for the result")

class StructuredAnswer(BaseModel):
    direct_answer: str = Field(description="질문의 핵심에 대한 직접적인 답변")
    background_info: str = Field(description="관련된 중요한 배경 정보")
    interesting_facts: str = Field(description="흥미로운 추가 사실들")
    easy_explanation: str = Field(description="어린이들이 이해하기 쉬운 설명")
    key_concepts: List[str] = Field(description="핵심 개념들")
    related_topics: List[str] = Field(description="관련 주제들")

class SearchResponse(BaseModel):
    question: str = Field(description="The original question that was searched")
    search_keywords: List[str] = Field(description="Keywords used for the search")
    search_results: List[SearchResult] = Field(description="List of search results")
    summary: str = Field(description="AI-generated summary based on search results")
    answer: StructuredAnswer = Field(description="Structured comprehensive answer to the question")
    genre: Optional[Genre] = Field(default=None, description="콘텐츠 장르")
    model_used: str = Field(description="The model that was used for processing")
    execution_time: Optional[str] = Field(description="Time taken to process the request")

    model_config = {"protected_namespaces": ()}

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수") 