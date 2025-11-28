"""Main Crawler Services - 의존성 주입"""
from fastapi import HTTPException
from app.core.config import settings
from app.services.main_crawler.web_crawler import MainCrawlerAgent
from app.services.main_crawler.analysis import CrawlerAnalysisService


def get_crawler_agent() -> MainCrawlerAgent:
    """Main Crawler Agent 인스턴스 반환 (FastAPI Depends용)"""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="LLM API key not configured"
        )
    return MainCrawlerAgent(llm_api_key=settings.openai_api_key)


def get_analysis_service() -> CrawlerAnalysisService:
    """Crawler Analysis Service 인스턴스 반환 (FastAPI Depends용)"""
    return CrawlerAnalysisService()


__all__ = [
    'MainCrawlerAgent',
    'CrawlerAnalysisService',
    'get_crawler_agent',
    'get_analysis_service'
]
