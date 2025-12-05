from fastapi import APIRouter, HTTPException, status
from app.models.language.play import (
    PlayRequest,
    PlayResponse,
    SupportedModelsResponse,
    SUPPORTED_PLAY_MODELS
)
from app.services.language.workflow.play import process_play_workflow_wrapper
from app.core.config import settings
from app.utils.logger.setup import setup_logger
import time

logger = setup_logger('play')

router = APIRouter(prefix="/play")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    연극(대본)에서 지원되는 AI 모델 목록을 반환합니다.
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_PLAY_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_PLAY_MODELS)
    )

@router.post("/generate", response_model=PlayResponse)
async def generate_play(request: PlayRequest) -> PlayResponse:
    """
    연극 제목과 대사로 연극 대사를 생성하는 API 엔드포인트
    """
    start_time = time.time()
    
    try:
        # 입력 데이터 검증
        if not request.llmText:
            logger.error("llmText was not provided.")
            raise HTTPException(
                status_code=500,
                detail="llmText가 전달되지 않았습니다."
            )
        
        result = await process_play_workflow_wrapper(request)
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time
        
        return result
        
    except Exception as e:
        logger.error(f"Error in play generation endpoint: {str(e)}")
        return PlayResponse(
            state="Incompleted",
            message=str(e),
            playTitle=None,
            script=[],
            execution_time=f"{time.time() - start_time:.2f}s"
        )

@router.get("/health")
async def play_health_check():
    """연극 대사 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Play",
        "description": "연극 대사 생성 서비스",
        "endpoints": [
            "/play/generate - 제목과 대사로 연극 대사 생성",
            "/play/health - 서비스 상태 확인"
        ]
    }