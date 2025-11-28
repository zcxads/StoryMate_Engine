"""
언어 모델 초기화 모듈
"""

from app.utils.language.generator import (
    language_generator,
    call_llm,
    call_llm_sync,
    get_available_models
)

# 기존 호환성을 위한 인스턴스들
from app.utils.language.interface import LanguageModel

# 기본 인스턴스 생성
default_language_model = LanguageModel(preferred="gpt-4o")

# 편의 함수들을 모듈 레벨에서 사용할 수 있도록 export
__all__ = [
    'language_generator',
    'call_llm', 
    'call_llm_sync',
    'get_available_models',
    'LanguageModel',
    'default_language_model'
]
