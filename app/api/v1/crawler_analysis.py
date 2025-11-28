from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time

from app.services.main_crawler import (
    MainCrawlerAgent,
    CrawlerAnalysisService,
    get_crawler_agent,
    get_analysis_service
)
from app.models.main_crawler.analysis import (
    CrawlerAnalysisRequest,
    CrawlerAnalysisResponse
)
from app.utils.logger.setup import setup_logger

logger = setup_logger('crawler_analysis')

router = APIRouter(prefix="/crawler_analysis")


@router.post("/analyze", response_model=CrawlerAnalysisResponse)
async def analyze_crawled_content(
    request: CrawlerAnalysisRequest,
    crawler_agent: MainCrawlerAgent = Depends(get_crawler_agent),
    analysis_service: CrawlerAnalysisService = Depends(get_analysis_service)
):
    """
    URL에서 본문을 크롤링하고 요약 + 워드 클라우드를 생성합니다.

    Returns:
        CrawlerAnalysisResponse: {
            "summary": "크롤링 결과 요약 텍스트",
            "ncp_url": "워드 클라우드 이미지 NCP URL"
        }
    """
    start_time = time.time()

    try:
        logger.info(f"📊 [API] 크롤링 분석 시작 - URL: {request.url}")

        # 1. 크롤링 수행
        crawl_result = await crawler_agent.extract_content_from_url(str(request.url))

        if crawl_result.get("error"):
            error_msg = crawl_result['error']
            logger.error(f"❌ [API] 크롤링 실패 - URL: {request.url}, 오류: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail="크롤링이 불가능한 컨텐츠입니다."
            )

        content = crawl_result.get("content")
        title = crawl_result.get("title")

        if not content:
            logger.error(f"❌ [API] 크롤링된 콘텐츠 없음 - URL: {request.url}")
            raise HTTPException(
                status_code=500,
                detail="크롤링이 불가능한 컨텐츠입니다."
            )

        logger.info(f"✅ [API] 크롤링 완료 - {len(content)} 문자")

        # 2. 분석 수행 (요약 + 워드 클라우드)
        analysis_result = await analysis_service.analyze_crawled_content(
            content=content,
            title=title
        )

        processing_time = time.time() - start_time

        logger.info(f"📊 [API] 분석 완료:")
        logger.info(f"   - 처리 시간: {processing_time:.2f}초")
        logger.info(f"   - 요약 길이: {len(analysis_result['summary'])} 문자")
        logger.info(f"   - 워드 클라우드: {analysis_result['ncp_url']}")

        return CrawlerAnalysisResponse(**analysis_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] 예외 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="크롤링이 불가능한 컨텐츠입니다."
        )


@router.get("/health")
async def analysis_health_check():
    """
    크롤러 분석 서비스 상태를 확인합니다.
    """
    return {
        "status": "healthy",
        "service": "crawler-analysis",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "웹 크롤링",
            "텍스트 요약",
            "키워드 추출",
            "워드 클라우드 생성",
            "NCP TMP 버킷 업로드"
        ]
    }
