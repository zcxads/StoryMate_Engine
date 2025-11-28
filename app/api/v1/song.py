from fastapi import APIRouter, HTTPException, status
from app.models.voice.song import SongRequest, SongResponse
from app.services.voice.song.generator import process_song_request
from app.utils.logger.setup import setup_logger
import time

logger = setup_logger('song')

router = APIRouter(prefix="/song")

@router.post("/generate", response_model=SongResponse)
async def generate_song(request: SongRequest) -> SongResponse:
    """
    노래 제목과 가사로 MP3 파일을 생성하는 API 엔드포인트
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting song generation for: {request.songTitle}")
        
        # 입력 데이터 검증
        if not request.lyrics or len(request.lyrics) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="가사(lyrics)는 반드시 제공되어야 합니다."
            )
        
        if not request.songTitle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="노래 제목(songTitle)은 반드시 제공되어야 합니다."
            )
        
        # 노래 생성 처리
        result = await process_song_request(request)
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        if hasattr(result, 'executionTimes'):
            result.executionTimes = {"total": execution_time}
        
        logger.info(f"Song generation completed with status: {result.state}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in song generation endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"노래 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def song_health_check():
    """노래 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Song",
        "description": "노래 생성 서비스",
        "endpoints": [
            "/song/generate - 제목과 가사로 노래 생성",
            "/song/health - 서비스 상태 확인"
        ]
    }
