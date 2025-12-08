"""
Content Category 분류 모델 정의
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.config import settings

class Genre(str, Enum):
    """콘텐츠 장르 분류"""
    SCIENCE = "science"           # 과학
    HISTORY = "history"           # 역사
    PHILOSOPHY = "philosophy"        # 철학
    LITERATURE = "literature"        # 문학
    ART_CULTURE = "art"   # 예술/문화
    PRACTICAL = "practical"         # 실용
    # OTHER = "기타"             # 기타

class ContentType(str, Enum):
    """생성 가능한 컨텐츠 타입"""
    VISUALIZATION = "visualization"  # 시각화(표,그래프,info)
    SONG = "song"                   # 노래
    THEATER = "theater"             # 연극모드  
    QUIZ = "quiz"                   # 퀴즈
    SUMMARY = "summary"             # 요약

class VisualizationType(str, Enum):
    """시각화 세부 타입"""
    TABLE = "table"           # 표
    CHART = "chart"          # 그래프/차트  
    INFOGRAPHIC = "infographic"  # 인포그래픽

class TextItem(BaseModel):
    """텍스트 아이템"""
    text: str = Field(..., description="텍스트 내용")

class PageText(BaseModel):
    """페이지별 텍스트 정보"""
    pageKey: int = Field(..., description="페이지 인덱스")
    texts: List[TextItem] = Field(..., description="해당 페이지의 텍스트 목록")

class ContentPossibility(BaseModel):
    """컨텐츠 생성 가능성 정보"""
    type: ContentType = Field(..., description="컨텐츠 타입")
    possible: bool = Field(..., description="생성 가능 여부")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0-1)")
    reason: str = Field(..., description="판단 근거")

class ContentCategoryRequest(BaseModel):
    """컨텐츠 카테고리 분류 요청"""
    llmText: List[PageText] = Field(..., description="페이지별 텍스트 데이터")
    model: Optional[str] = Field(default=settings.default_llm_model, description="사용할 LLM 모델")
    language: str = Field("ko", description="응답 언어 (ko, en, ja, zh)")

    def __init__(self, **data):
        super().__init__(**data)
        # 모델이 지정되지 않은 경우 중앙 설정 사용
        if not self.model:
            self.model = settings.default_llm_model

class ContentCategoryResponse(BaseModel):
    """컨텐츠 카테고리 분류 응답"""
    genre: Optional[Genre] = Field(None, description="콘텐츠 장르 (판별 불가 시 null)")

    # 각 기능별 가능 여부 (Boolean)
    song: bool = Field(..., description="노래 생성 가능 여부")
    play: bool = Field(..., description="연극 생성 가능 여부")
    quiz: bool = Field(..., description="퀴즈 생성 가능 여부")
    summary: bool = Field(..., description="요약 생성 가능 여부")
    visualization: bool = Field(..., description="시각화 생성 가능 여부")

    # 시각화 옵션 (visualization이 True일 때만)
    visualization_option: Optional[str] = Field(None, description="시각화 옵션 (chart 또는 table)")

    execution_time: Optional[str] = Field(None, description="실행 시간")

# 지원되는 모델 목록
SUPPORTED_CONTENT_CATEGORY_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class SupportedContentCategoryModelsResponse(BaseModel):
    """지원되는 모델 목록 응답"""
    supported_models: List[str] = Field(..., description="지원되는 모델 목록")
    default_model: str = Field(..., description="기본 모델")
    total_count: int = Field(..., description="지원되는 모델 수")