"""
언어 모델 생성기 - 통합 언어 모델을 사용한 간소화된 인터페이스
"""

import logging
from app.utils.language.generator import language_generator

logger = logging.getLogger(__name__)

class LanguageModel:
    """기존 호환성을 위한 래퍼 클래스"""

    def __init__(self, preferred: str = "gpt-4o"):
        self.preferred = preferred
        logger.info(f"LanguageModel initialized with preferred model: {preferred}")
    
    async def ainvoke(self, prompt, **kwargs):
        """비동기 호출"""
        try:
            return await language_generator.ainvoke(prompt, model=self.preferred, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.ainvoke: {e}")
            raise
    
    def invoke(self, prompt, **kwargs):
        """동기 호출"""
        try:
            return language_generator.invoke(prompt, model=self.preferred, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.invoke: {e}")
            raise
    
    def stream(self, prompt, **kwargs):
        """스트리밍 호출"""
        try:
            return language_generator.stream(prompt, model=self.preferred, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.stream: {e}")
            raise
    
    async def astream(self, prompt, **kwargs):
        """비동기 스트리밍 호출"""
        try:
            async for chunk in language_generator.astream(prompt, model=self.preferred, **kwargs):
                yield chunk
        except Exception as e:
            logger.error(f"Error in LanguageModel.astream: {e}")
            raise
