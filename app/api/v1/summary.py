from fastapi import APIRouter, HTTPException, status
from app.models.language.summary import (
    SummaryRequest,
    SummaryResponse,
    SupportedModelsResponse,
    SUPPORTED_SUMMARY_MODELS
)
from app.services.language.workflow.summary import process_summary_workflow_wrapper
from app.core.config import settings
import time

router = APIRouter(prefix="/summary")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    요약에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_SUMMARY_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_SUMMARY_MODELS)
    )

@router.post("/", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """책 내용 요약 생성"""
    start_time = time.time()
    
    try:
        result = await process_summary_workflow_wrapper(request)
        
        # 오류가 있는 경우 예외 발생
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "요약 생성 중 알 수 없는 오류가 발생했습니다.")
            )
        
        # 실행 시간 추가 (워크플로우에서 계산된 시간 사용)
        execution_time = result.get("execution_time", f"{time.time() - start_time:.2f}s")
        
        return SummaryResponse(
            summary=result["summary"],
            model_used=result["model_used"],
            page_count=result["page_count"],
            execution_time=execution_time
        )
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요약 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def summary_health_check():
    """요약 서비스 상태 확인"""
    from app.utils.language.generator import get_available_models
    
    available_models = get_available_models()
    
    return {
        "status": "healthy",
        "service": "Summary",
        "description": "책 내용 요약 생성 서비스",
        "available_models": available_models,
        "supported_models": SUPPORTED_SUMMARY_MODELS
    } 