from fastapi import APIRouter, HTTPException, status
from app.models.language.lyrics import (
    SongLyricsRequest,
    SongLyricsResponse,
    SupportedModelsResponse,
    SUPPORTED_LYRICS_MODELS
)
from app.services.language.workflow.lyrics import process_lyrics_workflow_wrapper
from app.config import settings
import time

router = APIRouter(prefix="/lyrics")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    가사 생성에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_LYRICS_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_LYRICS_MODELS)
    )

@router.post("/", response_model=SongLyricsResponse)
async def generate_song_lyrics(request: SongLyricsRequest):
    """텍스트 기반 노래 가사 생성"""
    start_time = time.time()
    
    try:
        # 입력 데이터 검증
        if not request.processedLlmText and not request.llmText:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="processedLlmText 또는 llmText 중 하나는 반드시 제공되어야 합니다."
            )
        
        result = await process_lyrics_workflow_wrapper(request)
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"가사 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def lyrics_health_check():
    """가사 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Lyrics",
        "description": "노래 가사 생성 서비스"
    }
