from fastapi import APIRouter, HTTPException, status
from app.models.language.all import (
    AllRequest,
    SupportedModelsResponse,
    SUPPORTED_ALL_MODELS
)
from app.services.language.workflow.all import process_all_workflow_wrapper
from app.core.config import settings
import time

router = APIRouter(prefix="/all")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    통합 처리(OCR + Sound + Quiz)에서 지원되는 AI 모델 목록을 반환합니다.

    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_ALL_MODELS,
        default_model=settings.llm_text_processing_model,
        total_count=len(SUPPORTED_ALL_MODELS)
    )

@router.post("/")
async def process_all(request: AllRequest):
    """통합 처리 (OCR + Sound + Quiz)"""
    start_time = time.time()
    
    try:
        result = await process_all_workflow_wrapper(request)
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통합 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def all_health_check():
    """통합 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "All",
        "description": "OCR, Sound, Quiz 통합 처리 서비스"
    }
