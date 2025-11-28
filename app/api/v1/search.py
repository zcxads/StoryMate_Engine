"""
검색 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.models.language.search import (
    SearchRequest, 
    SearchResponse, 
    SupportedModelsResponse,
    SUPPORTED_SEARCH_MODELS
)
from app.services.language.workflow.search import process_search_workflow_wrapper
from app.core.config import settings

# 라우터 생성
router = APIRouter(prefix="/search")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    검색에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_SEARCH_MODELS,
        default_model=settings.llm_text_processing_model,
        total_count=len(SUPPORTED_SEARCH_MODELS)
    )

@router.post("/", response_model=Dict[str, Any])
async def search_web(request: SearchRequest) -> Dict[str, Any]:
    """
    웹 검색을 수행하고 결과를 분석합니다.
    
    Args:
        request: 검색 요청 (질문, 검색 키워드, 모델 등)
        
    Returns:
        Dict[str, Any]: 검색 결과와 AI 분석 응답
    """
    try:
        # 검색 워크플로우 처리
        result = await process_search_workflow_wrapper(request)
        return result
        
    except ValueError as e:
        # 모델 검증 오류
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검색 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def search_health_check() -> Dict[str, str]:
    """
    검색 서비스 헬스체크 엔드포인트
    
    Returns:
        Dict[str, str]: 서비스 상태 정보
    """
    return {
        "status": "healthy",
        "service": "search",
        "message": "검색 서비스가 정상적으로 작동 중입니다."
    } 