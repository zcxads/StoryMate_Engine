from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time

from app.services.main_crawler import MainCrawlerAgent, get_crawler_agent
from app.models.main_crawler.web_crawler import (
    MainCrawlRequest,
    MainCrawlResponse,
    SUPPORTED_MAIN_CRAWLER_MODELS,
    SupportedMainCrawlerModelsResponse
)
from app.config import settings
from app.utils.logger.setup import setup_logger

logger = setup_logger('main_crawler')

router = APIRouter(prefix="/main_crawler")

@router.get("/models", response_model=SupportedMainCrawlerModelsResponse)
async def get_supported_models() -> SupportedMainCrawlerModelsResponse:
    """메인 크롤러에서 지원되는 AI 모델 목록을 반환합니다."""
    return SupportedMainCrawlerModelsResponse(
        supported_models=SUPPORTED_MAIN_CRAWLER_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_MAIN_CRAWLER_MODELS)
    )

@router.post("/crawl", response_model=MainCrawlResponse)
async def extract_content(
    request: MainCrawlRequest,
    agent: MainCrawlerAgent = Depends(get_crawler_agent)
):
    """URL에서 본문을 즉시 추출하고 결과를 반환합니다."""
    start_time = time.time()

    try:
        result = await agent.extract_content_from_url(str(request.url))

        # 처리 시간 추가
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time

        # 에러 발생 시 500 에러로 통일
        if result.get("error"):
            error_msg = result['error']
            logger.error(f"❌ [API] 본문 추출 실패 - URL: {request.url}, 오류: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail="크롤링이 불가능한 컨텐츠입니다."
            )

        # 성공 로그
        content_length = len(result.get("content", "")) if result.get("content") else 0
        logger.info(f"📊 [API] 결과 요약:")
        logger.info(f"   - 처리 시간: {processing_time:.2f}초")
        logger.info(f"   - 추출 길이: {content_length}자")
        logger.info(f"   - 제목: {result.get('title', 'N/A')}")

        return MainCrawlResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] 예외 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="크롤링이 불가능한 컨텐츠입니다."
        )

@router.get("/health")
async def extraction_health_check():
    """
    서비스 상태를 확인합니다.
    """
    return {
        "status": "healthy",
        "service": "main-crawler-agent",
        "timestamp": datetime.now().isoformat()
    }
    