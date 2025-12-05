from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from app.core.config import settings

class GenderType(str, Enum):
    """성별 타입"""
    MALE = "남자"
    FEMALE = "여자"
    NEUTRAL = "중성"

    @classmethod
    def get_default(cls) -> 'GenderType':
        """기본 성별 힌트 반환"""
        return cls.MALE
    
class TTSRequest(BaseModel):
    """TTS 생성 요청 모델"""
    texts: List[str] = Field(..., description="TTS로 변환할 텍스트 리스트", examples=[["안녕하세요, TTS 테스트입니다."]])
    gender_hints: Optional[List[GenderType]] = Field(None, description="각 텍스트의 성별 힌트", examples=[["남자"]])
    voices: Optional[List[str]] = Field(None, description="사용할 목소리 리스트 (지정하지 않으면 기본 목소리 사용)", examples=[["echo"]])
    batch_size: Optional[int] = Field(3, description="동시 처리할 배치 크기", ge=1, le=10)

class SingleTTSRequest(BaseModel):
    """단일 TTS 생성 요청 모델"""
    text: str = Field(..., description="TTS로 변환할 텍스트", examples=["안녕하세요, TTS 테스트입니다."])
    voice: Optional[str] = Field(None, description="사용할 목소리 (None이면 provider와 성별에 따라 자동 선택)")
    gender_hint: Optional[GenderType] = Field(GenderType.MALE, description="성별 힌트")
    
class PlayTTSRequest(BaseModel):
    script: List[str] = []
    playTitle: Optional[str] = None
    language: Optional[str] = None

class TTSJobStatus(str, Enum):
    """TTS 작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TTSResponse(BaseModel):
    """TTS 생성 응답 모델"""
    job_id: str = Field(..., description="작업 ID")
    status: TTSJobStatus = Field(..., description="작업 상태")
    message: str = Field(..., description="응답 메시지")
    total_files: Optional[int] = Field(None, description="생성될 총 파일 수")
    completed_files: Optional[int] = Field(None, description="완료된 파일 수")
    files: Optional[List[str]] = Field(None, description="생성된 파일 경로 리스트")

class SingleTTSResponse(BaseModel):
    """단일 TTS 생성 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    filename: Optional[str] = Field(None, description="생성된 파일명")
    file_path: Optional[str] = Field(None, description="생성된 파일 경로")
    download_url: Optional[str] = Field(None, description="파일 다운로드 URL")
    ncp_url: Optional[str] = Field(None, description="NCP 업로드 URL")
    duration: Optional[float] = Field(None, description="TTS 재생 시간 (초 단위)")

class JobStatusResponse(BaseModel):
    """작업 상태 조회 응답 모델"""
    job_id: str = Field(..., description="작업 ID")
    status: TTSJobStatus = Field(..., description="작업 상태")
    progress: float = Field(..., description="진행률 (0.0 ~ 1.0)", ge=0.0, le=1.0)
    total_files: int = Field(..., description="총 파일 수")
    completed_files: int = Field(..., description="완료된 파일 수")
    failed_files: int = Field(..., description="실패한 파일 수")
    files: List[Dict[str, Any]] = Field(..., description="파일별 상세 정보")

class VoiceListResponse(BaseModel):
    """목소리 목록 응답 모델"""
    all_voices: List[str] = Field(..., description="모든 사용 가능한 목소리")
    male_voices: List[str] = Field(..., description="남성 목소리")
    female_voices: List[str] = Field(..., description="여성 목소리")

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")

# 지원되는 TTS 모델 목록
SUPPORTED_TTS_MODELS = [
    "gemini-2.5-flash-preview-tts",
    "gpt-4o-mini-tts"
]

class SupportedTTSModelsResponse(BaseModel):
    """지원되는 TTS 모델 응답"""
    supported_models: List[str] = Field(default=SUPPORTED_TTS_MODELS, description="지원되는 모델 목록")
    default_model: str = Field(default=settings.openai_tts_model, description="기본 모델")
    total_count: int = Field(default=len(SUPPORTED_TTS_MODELS), description="총 모델 수")