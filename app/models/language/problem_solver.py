"""
고도화된 문제 풀이 API를 위한 모델 정의
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_PROBLEM_SOLVER_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class ProblemType(Enum):
    """문제 유형 분류"""
    VALID_SINGLE = "valid_single"  # 정상적인 단일 문제
    INVALID = "invalid"            # 비정상적인 문제 (모든 경우 통합)

class ProblemSolverRequest(BaseModel):
    """고도화된 문제 풀이 요청 모델"""

    problem_images: List[str] = Field(
        description="Base64 encoded images of the problem (단일/다중 이미지 통합)"
    )
    model: str = Field(
        description="Language model to use for processing",
        default=settings.llm_advanced_analysis_model
    )
    language: str = Field(
        description="Response language (ko, en, ja, zh)",
        default="ko"
    )
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_PROBLEM_SOLVER_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_PROBLEM_SOLVER_MODELS)}")
        return v
    
    @validator('language')
    def validate_language(cls, v):
        supported_languages = ["ko", "en", "ja", "zh"]
        if v not in supported_languages:
            raise ValueError(f"지원되지 않는 언어입니다. 지원 언어: {', '.join(supported_languages)}")
        return v

    @validator('problem_images')
    def validate_problem_images(cls, v):
        if not v or len(v) == 0:
            raise ValueError("problem_images는 반드시 제공되어야 하며 빈 리스트일 수 없습니다.")

        if len(v) > 5:  # 최대 5개 이미지 제한
            raise ValueError("최대 5개의 이미지까지만 업로드 가능합니다.")

        return v
    
    model_config = {"protected_namespaces": ()}

class ProblemValidationResult(BaseModel):
    """문제 이미지 검증 결과"""
    
    is_valid: bool = Field(description="문제 이미지가 유효한지 여부")
    problem_type: ProblemType = Field(description="감지된 문제 유형")
    confidence: float = Field(description="감지 신뢰도 (0.0-1.0)")
    message: str = Field(description="사용자에게 표시할 메시지")
    details: Optional[Dict[str, Any]] = Field(default=None, description="추가 세부 정보")

class ProblemSolverResponse(BaseModel):
    """고도화된 문제 풀이 응답 모델
    
    유횤한 문제: answer, explanation, concepts, execution_time
    무효한 문제: message만 반환
    """
    
    # 문제가 유효한 경우의 응답 필드들
    answer: Optional[str] = Field(default=None, description="문제의 답")
    explanation: Optional[str] = Field(default=None, description="상세한 풀이 과정")
    concepts: Optional[str] = Field(default=None, description="핵심 개념")
    execution_time: Optional[str] = Field(default=None, description="처리 시간")
    
    # 비정상 문제인 경우의 메시지
    message: Optional[str] = Field(default=None, description="비정상 문제 시 사용자 메시지")
    
    model_config = {
        "protected_namespaces": (),
    }
    
    def model_dump(self, **kwargs):
        """None 값을 제외한 딕셔너리 반환"""
        kwargs.setdefault('exclude_none', True)
        return super().model_dump(**kwargs)


class SupportedProblemSolverModelsResponse(BaseModel):
    """지원되는 모델 응답"""
    
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")

class ProblemDetectionRequest(BaseModel):
    """Google Vision OCR 기반 문제 검출 요청 모델"""

    problem_image: str = Field(description="Base64 encoded image containing multiple problems")
    model_config = {"protected_namespaces": ()}

class ProblemDetectionResponse(BaseModel):
    """Google Vision OCR 기반 문제 검출 응답 모델"""

    file_path: str = Field(description="크롭된 문제 이미지 파일 경로")
    execution_time: str = Field(description="처리 시간")
    error: Optional[str] = Field(default=None, description="오류 메시지 (실패 시)")
