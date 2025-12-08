from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from app.config import settings

# 지원되는 메인 크롤러 모델 목록 (전역 통일)
SUPPORTED_MAIN_CRAWLER_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class MainCrawlRequest(BaseModel):
    """메인 웹 크롤링 요청 모델"""
    url: HttpUrl

class MainCrawlResponse(BaseModel):
    """메인 웹 크롤링 응답 모델"""
    title: Optional[str] = None
    content: Optional[str] = None
    
    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True


class SupportedMainCrawlerModelsResponse(BaseModel):
    """지원되는 메인 크롤러 모델 응답"""
    supported_models: List[str] = SUPPORTED_MAIN_CRAWLER_MODELS
    default_model: str = settings.default_llm_model
    total_count: int = len(SUPPORTED_MAIN_CRAWLER_MODELS)
