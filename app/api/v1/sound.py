from fastapi import APIRouter, HTTPException, status
from app.models.language.sound import (
    SoundRequest,
    SupportedModelsResponse,
    SUPPORTED_SOUND_MODELS
)
from app.services.language.workflow.sound import process_sound_workflow_wrapper
from app.core.config import settings
import time

router = APIRouter(prefix="/sound")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    사운드 생성에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_SOUND_MODELS,
        default_model=settings.llm_text_processing_model,
        total_count=len(SUPPORTED_SOUND_MODELS)
    )

@router.post("/")
async def generate_sound(request: SoundRequest):
    """텍스트 기반 사운드 및 배경음악 생성"""
    start_time = time.time()
    
    try:
        result = await process_sound_workflow_wrapper(request)
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사운드 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def sound_health_check():
    """사운드 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Sound",
        "description": "배경음악 및 효과음 생성 서비스"
    }
