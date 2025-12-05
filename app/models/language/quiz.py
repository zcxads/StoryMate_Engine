from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from enum import IntEnum
from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_QUIZ_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

# 문제 유형 정의
class ProblemType(IntEnum):
    OX = 0          # OX 문제
    TWO_CHOICE = 2  # 이지선다
    THREE_CHOICE = 3  # 삼지선다
    FOUR_CHOICE = 4  # 사지선다
    FIVE_CHOICE = 5  # 오지선다

# 문제 유형 설명 매핑
PROBLEM_TYPE_DESCRIPTIONS = {
    ProblemType.OX: "OX 문제 (참/거짓)",
    ProblemType.TWO_CHOICE: "이지선다 문제",
    ProblemType.THREE_CHOICE: "삼지선다 문제",
    ProblemType.FOUR_CHOICE: "사지선다 문제",
    ProblemType.FIVE_CHOICE: "오지선다 문제",
}

class QuizItem(BaseModel):
    id: str
    question: str
    answer: str
    options: List[str]
    problemType: int

class QuizResponse(BaseModel):
    state: str
    quizs: List[QuizItem]
    execution_time: Optional[str] = Field(None, description="API execution time")

class QuizRequest(BaseModel):
    """텍스트 기반 퀴즈 생성 요청 모델"""
    model: str = Field(description="Language model to use for processing", default=settings.default_llm_model)
    llmText: List[Dict[str, Any]]
    quizCount: int = Field(
        default=10,
        description="생성할 퀴즈 개수"
    )
    problemType: Optional[Union[int, List[int]]] = Field(
        default=None,
        description="생성할 문제 유형 (0: OX, 2: 이지선다, 3: 삼지선다, 4: 사지선다, 5: 오지선다). 단일 정수 또는 정수 배열로 지정 가능. 미지정 시 랜덤하게 생성."
    )

    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_QUIZ_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_QUIZ_MODELS)}")
        return v

    @validator('problemType')
    def validate_problem_type(cls, v):
        if v is None:
            return None

        valid_types = [pt.value for pt in ProblemType]

        if isinstance(v, list):
            for pt in v:
                if pt not in valid_types:
                    raise ValueError(f"지원되지 않는 문제 유형입니다: {pt}. 지원되는 유형: {valid_types}")
            return v
        elif isinstance(v, int):
            if v not in valid_types:
                raise ValueError(f"지원되지 않는 문제 유형입니다: {v}. 지원되는 유형: {valid_types}")
            return v
        else:
            raise ValueError(f"문제 유형은 정수 또는 정수 배열이어야 합니다.")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")

class SupportedProblemTypesResponse(BaseModel):
    problem_types: Dict[int, str] = Field(description="지원되는 문제 유형 목록")
    total_count: int = Field(description="총 문제 유형 수")
