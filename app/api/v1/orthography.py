from fastapi import APIRouter, HTTPException, status
from app.models.language.orthography import (
    OrthographyRequest,
    OrthographyResponse,
    SupportedModelsResponse,
    SUPPORTED_ORTHOGRAPHY_MODELS
)
from app.services.language.workflow.orthography import process_orthography_workflow_wrapper
from app.core.config import settings

router = APIRouter(prefix="/orthography")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    맞춤법 교정에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_ORTHOGRAPHY_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_ORTHOGRAPHY_MODELS)
    )

@router.post("/", response_model=OrthographyResponse)
async def process_orthography(request: OrthographyRequest):
    """맞춤법 교정 및 텍스트 처리 (언어 감지 포함)"""
    try:
        result = await process_orthography_workflow_wrapper(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"맞춤법 교정 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def orthography_health_check():
    """텍스트 교정 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Orthography",
        "description": "텍스트 전처리 및 교정 서비스"
    }
