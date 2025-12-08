from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union

from app.models.language.content_category import Genre
from app.config import settings

class FingerDetectionRequest(BaseModel):
    """손가락 가리키기 인식 요청 모델"""

    # 필수 필드
    image_data: str = Field(
        ...,
        description="손가락으로 가리킨 이미지 데이터 (Base64 인코딩)",
        min_length=1
    )

    # LLM 설정
    model: Optional[str] = Field(
        default=settings.default_llm_model,
        description="사용할 LLM 모델"
    )

    # 분석 모드
    mode: Optional[str] = Field(
        default="finger_detection",
        description="분석 모드 (finger_detection | document_reading)"
    )

    # 언어 설정
    language: Optional[str] = Field(
        default="ko",
        description="응답 언어 (ko: 한국어, en: 영어, ja: 일본어)"
    )
    

class FingerDetectionSuccessResponse(BaseModel):
    """정상적인 손가락 가리키기 인식 응답 모델"""

    detected_word: str = Field(
        ...,
        description="손가락으로 가리킨 정확한 단어 또는 문장"
    )

    meaning: str = Field(
        ...,
        description="검출된 단어/문장의 뜻과 의미"
    )

    explanation: str = Field(
        ...,
        description="검출된 단어/문장에 대한 자세한 설명 (문맥, 사용법, 예시 포함)"
    )

    ncp_url: Optional[str] = Field(
        default=None,
        description="검출된 단어/문장의 발음 TTS 오디오 URL (NCP)"
    )

    genre: Optional[Genre] = Field(
        default=None,
        description="콘텐츠 장르"
    )

    execution_time: str = Field(
        ...,
        description="실행 시간"
    )

class FingerDetectionEmptyResponse(BaseModel):
    """허공 가리키기 감지 시 응답 모델"""
    
    message: str = Field(
        ...,
        description="재업로드 요청 메시지"
    )

class FingerDetectionNoFingerResponse(BaseModel):
    """손가락이 없는 이미지 감지 시 응답 모델"""
    
    message: str = Field(
        ...,
        description="손가락 인식 실패 메시지"
    )

# 하위 호환성을 위한 기존 모델 유지 (Union 타입 사용)
FingerDetectionSimpleResponse = Union[FingerDetectionSuccessResponse, FingerDetectionEmptyResponse, FingerDetectionNoFingerResponse]

class DocumentReadingResponse(BaseModel):
    """문서 읽기 분석 응답 모델"""

    # 분석 결과
    markdown_content: str = Field(
        ...,
        description="마크다운으로 구조화된 문서 내용"
    )

    detected_language: Optional[str] = Field(
        default=None,
        description="감지된 언어 코드"
    )

    document_type: Optional[str] = Field(
        default=None,
        description="문서 유형"
    )

    genre: Optional[Genre] = Field(
        default=None,
        description="콘텐츠 장르"
    )

    execution_time: str = Field(
        ...,
        description="실행 시간"
    )

class ImageToBase64Response(BaseModel):
    """이미지를 Base64로 변환한 응답 모델"""
    
    # 변환 결과
    image_data: str = Field(
        ...,
        description="Base64로 인코딩된 이미지 데이터"
    )
    
    # 메타데이터
    file_size: str = Field(
        ...,
        description="원본 파일 크기"
    )
    
    image_format: str = Field(
        ...,
        description="이미지 형식"
    )
    
    base64_size: str = Field(
        ...,
        description="Base64 인코딩된 데이터 크기"
    )

# 지원되는 손가락 인식 모델 목록 (전역 통일)
SUPPORTED_FINGER_DETECTION_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class SupportedFingerDetectionModelsResponse(BaseModel):
    """지원되는 손가락 인식 모델 응답"""
    
    supported_models: List[str] = Field(
        default=SUPPORTED_FINGER_DETECTION_MODELS,
        description="지원되는 모델 목록"
    )
    
    default_model: str = Field(
        default=settings.default_llm_model,
        description="기본 모델"
    )
    
    total_count: int = Field(
        default=len(SUPPORTED_FINGER_DETECTION_MODELS),
        description="총 모델 수"
    )
    
    features: Dict[str, bool] = Field(
        default={
            "image_analysis": True,
            "finger_pointing_detection": True,
            "object_recognition": True,
            "confidence_scoring": True,
            "multilingual_support": True
        },
        description="지원되는 기능 목록"
    )