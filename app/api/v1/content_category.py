"""
컨텐츠 카테고리 분류 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.language.content_category import (
    ContentCategoryRequest,
    ContentCategoryResponse,
    SupportedContentCategoryModelsResponse,
    SUPPORTED_CONTENT_CATEGORY_MODELS
)
from app.services.language.content_category import ContentCategoryAnalyzer
from app.config import settings
import time

# 로깅 설정
from app.utils.logger.setup import setup_logger
logger = setup_logger('content_category')

router = APIRouter(prefix="/content-category")

# 컨텐츠 카테고리 분석 서비스 인스턴스
content_analyzer = ContentCategoryAnalyzer()

@router.get("/models", response_model=SupportedContentCategoryModelsResponse)
async def get_supported_models() -> SupportedContentCategoryModelsResponse:
    """
    컨텐츠 카테고리 분류에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedContentCategoryModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedContentCategoryModelsResponse(
        supported_models=SUPPORTED_CONTENT_CATEGORY_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_CONTENT_CATEGORY_MODELS)
    )

@router.post("/analyze-text", response_model=ContentCategoryResponse)
async def analyze_content_from_text(request: ContentCategoryRequest):
    """
    텍스트를 직접 입력받아 컨텐츠 카테고리 분석을 수행합니다.

    - 입력된 텍스트를 분석하여 문서 타입을 분류
    - 시각화, 노래, 연극모드, 퀴즈, 요약 등 각 컨텐츠 생성 가능성 판단
    - 추천 컨텐츠 타입 제공
    """
    try:
        start_time = time.time()  # 전체 처리 시간 측정 시작
        if not request.llmText or len(request.llmText) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="분석할 텍스트가 제공되지 않았습니다."
            )

        result = await content_analyzer.analyze_content(request)

        # 전체 처리 시간 계산 및 결과에 적용 (텍스트 기반)
        total_time = time.time() - start_time
        result.execution_time = f"{total_time:.2f}s"

        return JSONResponse(
            content=result.model_dump(),
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"컨텐츠 카테고리 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def content_category_health_check():
    """컨텐츠 카테고리 분류 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Content Category Analyzer",
        "description": "문서 분석 및 컨텐츠 생성 가능성 판단 서비스",
        "features": [
            "문서 타입 자동 분류",
            "컨텐츠 생성 가능성 분석",
            "추천 컨텐츠 타입 제공",
            "다국어 지원"
        ],
        "supported_models": SUPPORTED_CONTENT_CATEGORY_MODELS,
        "supported_languages": ["ko", "en", "ja", "zh"],
        "content_features": ["song", "play", "quiz", "summary", "visualization"],
        "genres": ["science", "history", "philosophy", "literature", "art", "practical"]
    }