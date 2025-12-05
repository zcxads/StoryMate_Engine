from pydantic import BaseModel, Field, field_validator, model_validator, validator
from typing import List, Dict, Optional, Union, Any
from app.core.config import settings

# 지원되는 연극(대본) 모델 목록 (전역 통일)
SUPPORTED_PLAY_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class TextItem(BaseModel):
    text: str

class PageItem(BaseModel):
    pageKey: int
    texts: List[TextItem]

class PlayRequest(BaseModel):
    model: Optional[str] = Field(default=settings.default_llm_model, description="Language model to use for processing")
    llmText: Optional[List[PageItem]] = Field(None, description="Page-based text format")
    language: Optional[str] = Field(description="Language code", default=settings.language_code[0])

    def __init__(self, **data):
        super().__init__(**data)
        # 모델이 지정되지 않은 경우 중앙 설정 사용
        if not self.model:
            self.model = settings.default_llm_model

class PlayResponse(BaseModel):
    state: str
    message: Optional[str] = None
    playTitle: Optional[str] = None
    script: Union[List[str], Dict[str, List[str]]]
    execution_time: Optional[str] = Field(None, description="API execution time")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(default=SUPPORTED_PLAY_MODELS, description="지원되는 모델 목록")
    default_model: str = Field(default=settings.default_llm_model, description="기본 모델")
    total_count: int = Field(default=len(SUPPORTED_PLAY_MODELS), description="총 모델 수")
