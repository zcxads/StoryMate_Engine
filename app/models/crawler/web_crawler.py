from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum

class CrawlerStatus(str, Enum):
    """크롤링 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CrawlRequest(BaseModel):
    """웹 크롤링 요청 모델"""
    url: HttpUrl

class CrawlResponse(BaseModel):
    """웹 크롤링 응답 모델"""
    url: str
    status: CrawlerStatus
    title: Optional[str] = None
    content: Optional[str] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    
    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True

class CrawlJob(BaseModel):
    """크롤링 작업 모델"""
    job_id: str
    url: str
    status: CrawlerStatus
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[CrawlResponse] = None
    error_message: Optional[str] = None
    
    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True

class CrawlStats(BaseModel):
    """크롤링 통계 모델"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_content_length: int = 0
