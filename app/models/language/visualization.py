from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from enum import Enum
from app.models.language.content_category import Genre
from app.core.config import settings

class VisualizationType(str, Enum):
    """시각화 유형"""
    TABLE = "table"
    CHART = "chart"

class VisualizationCategory(str, Enum):
    """시각화 카테고리"""
    TABLE = "표"
    CHART = "차트"

class OutputFormat(str, Enum):
    """출력 형식"""
    IMAGE_PNG = "image_png"

class VisualizationGenerateRequest(BaseModel):
    """시각화 생성 요청 모델"""

    text: Optional[str] = Field(
        default=None,
        description="시각화할 텍스트 내용",
        min_length=1
    )

    file: Optional[str] = Field(
        default=None,
        description="업로드된 파일 (multipart/form-data)"
    )

    category: str = Field(
        ...,
        description="시각화 카테고리 (표, 차트)"
    )

    genre: Optional[Genre] = Field(
        default=None,
        description="콘텐츠 장르 (선택사항)"
    )

    model: str = Field(
        default=settings.llm_visualization_model,
        description="사용할 LLM 모델"
    )

    language: Optional[str] = Field(
        default=settings.language_code[0],
        description="분석 및 TTS 생성 언어 (ko, en, ja, zh 등)"
    )

class VisualizationRequest(BaseModel):
    """문서 시각화 요청 모델 (내부 사용)"""

    # 필수 필드
    content: str = Field(
        ...,
        description="시각화할 문서 내용 (OCR 처리된 텍스트)",
        min_length=1
    )

    category: VisualizationCategory = Field(
        ...,
        description="시각화 카테고리 (표, 차트)"
    )

    # 선택 필드 (호환성을 위해 유지, 하지만 category에서 자동 변환)
    visualization_type: Optional[VisualizationType] = Field(
        default=None,
        description="시각화 유형 (category에서 자동 설정됨)"
    )

    # LLM 설정
    model: Optional[str] = Field(
        default=settings.llm_visualization_model,
        description="사용할 LLM 모델"
    )
    
    # 표 특화 옵션
    table_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="표 생성 옵션 (컬럼 수, 정렬 방식 등)"
    )
    
    # 차트 특화 옵션
    chart_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="차트 생성 옵션 (차트 타입, 색상 등)"
    )
    
    # 이미지 변환 옵션
    image_options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "width": 800,
            "height": 600,
            "quality": 90,
            "background_color": "white"
        },
        description="이미지 변환 옵션"
    )
    
    def model_post_init(self, __context):
        """카테고리에서 visualization_type으로 자동 변환"""
        if self.visualization_type is None:
                    # 카테고리를 visualization_type으로 변환
            category_mapping = {
                VisualizationCategory.TABLE: VisualizationType.TABLE,
                VisualizationCategory.CHART: VisualizationType.CHART
            }
            self.visualization_type = category_mapping.get(self.category, VisualizationType.TABLE)

class VisualizationContent(BaseModel):
    """시각화 콘텐츠 항목"""
    viz_ncp_url: str = Field(
        ...,
        description="시각화 이미지 NCP URL"
    )

    analysis_text: str = Field(
        default="",
        description="시각화에 대한 분석 텍스트"
    )

    tts_ncp_url: str = Field(
        default="",
        description="분석 텍스트 TTS NCP URL"
    )

class VisualizationResponse(BaseModel):
    """문서 시각화 응답 모델"""
    visualization_type: str = Field(
        ...,
        description="생성된 시각화 유형"
    )

    genre: str = Field(
        ...,
        description="콘텐츠 장르"
    )

    execution_time: str = Field(
        ...,
        description="전체 실행 시간"
    )

    contents: List[VisualizationContent] = Field(
        default_factory=list,
        description="시각화 콘텐츠 목록 (순서 보장)"
    )

class VisualizationError(BaseModel):
    """시각화 오류 응답 모델"""
    
    error_type: str = Field(
        ...,
        description="오류 유형"
    )
    
    error_message: str = Field(
        ...,
        description="오류 메시지"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 오류 세부정보"
    )

# 지원되는 시각화 모델 목록 (전역 통일)
SUPPORTED_VISUALIZATION_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class FileTextExtractionResponse(BaseModel):
    """파일 텍스트 추출 응답 모델"""

    extracted_text: str = Field(
        ...,
        description="추출된 텍스트 내용"
    )

    file_type: str = Field(
        ...,
        description="파일 형식 (csv, excel 등)"
    )

    execution_time: str = Field(
        ...,
        description="실행 시간"
    )

class SupportedVisualizationModelsResponse(BaseModel):
    """지원되는 시각화 모델 응답"""

    supported_models: List[str] = Field(
        default=SUPPORTED_VISUALIZATION_MODELS,
        description="지원되는 모델 목록"
    )

    default_model: str = Field(
        default=settings.llm_visualization_model,
        description="기본 모델"
    )

    total_count: int = Field(
        default=len(SUPPORTED_VISUALIZATION_MODELS),
        description="총 모델 수"
    )

    visualization_types: List[str] = Field(
        default=[vt.value for vt in VisualizationType],
        description="지원되는 시각화 유형"
    )

    visualization_categories: List[str] = Field(
        default=[vc.value for vc in VisualizationCategory],
        description="지원되는 시각화 카테고리"
    )

    output_formats: List[str] = Field(
        default=[of.value for of in OutputFormat],
        description="지원되는 출력 형식"
    )
