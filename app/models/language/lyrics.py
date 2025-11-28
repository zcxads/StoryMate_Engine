from pydantic import BaseModel, Field, field_validator, model_validator, validator
from typing import List, Dict, Optional, Union, Any

from app.core.config import settings

# 지원되는 모델 목록 (전역 통일)
SUPPORTED_LYRICS_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash", 
    "gemini-2.0-flash",
    "gpt-5",
    "gpt-5-mini",
    "gpt-4o",
    "gpt-4o-mini"
]

class CharacterContent(BaseModel):
    text: str

class TextItem(BaseModel):
    text: str

class PageItem(BaseModel):
    pageKey: int
    texts: List[TextItem]

class SongLyricsRequest(BaseModel):
    model: str = Field(description="Language model to use for processing", default=settings.llm_text_processing_model)
    processedLlmText: Optional[List[CharacterContent]] = Field(None, description="Character content format")
    llmText: Optional[List[PageItem]] = Field(None, description="Page-based text format")
    language: Optional[str] = Field(description="Language code", default=settings.language_code[0])
    
    @validator('model')
    def validate_model(cls, v):
        if v not in SUPPORTED_LYRICS_MODELS:
            raise ValueError(f"지원되지 않는 모델입니다. 지원 모델: {', '.join(SUPPORTED_LYRICS_MODELS)}")
        return v
    
    @model_validator(mode='after')
    def validate_input_format(self):
        """processedLlmText와 llmText 중 하나는 반드시 제공되어야 함"""
        if not self.processedLlmText and not self.llmText:
            raise ValueError('processedLlmText 또는 llmText 중 하나는 반드시 제공되어야 합니다.')
        return self


class SongLyricsResponse(BaseModel):
    state: str
    songTitle: Optional[str] = None
    lyrics: Union[List[str], Dict[str, List[str]]]
    execution_time: Optional[str] = Field(None, description="API execution time")

class SupportedModelsResponse(BaseModel):
    supported_models: List[str] = Field(description="지원되는 모델 목록")
    default_model: str = Field(description="기본 모델")
    total_count: int = Field(description="총 모델 수")
