"""
통합 언어 모델 관리자 (LangChain 호환 버전)
API 요청에서 모델을 받고, 환경변수로 설정을 관리
"""

import os
import asyncio
from app.utils.logger.setup import setup_logger
from typing import Optional, Dict, Any, Union, List
from langchain_core.runnables.base import Runnable
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.outputs import LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun

from app.core.config import settings

logger = setup_logger('language_generator')

class UnifiedLanguageModel(Runnable):
    """통합 언어 모델 클래스 - 환경변수 기반 설정 및 LangChain 호환"""
    
    def __init__(self):
        super().__init__()
        self.models: Dict[str, Optional[Runnable]] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """사용 가능한 모든 언어 모델을 환경변수 설정으로 초기화합니다."""
        
        # OpenAI 모델 초기화
        try:
            from langchain_openai import ChatOpenAI
            openai_model = settings.openai_model
            
            if "gpt-5" in openai_model.lower():
                # GPT-5 models don't support temperature parameter
                self.models["openai"] = ChatOpenAI(
                    model=openai_model,
                    max_tokens=int(settings.openai_max_tokens),
                    api_key=os.getenv("OPENAI_API_KEY"),
                )
            else:
                self.models["openai"] = ChatOpenAI(
                    model=openai_model,
                    temperature=float(settings.openai_temperature),
                    max_tokens=int(settings.openai_max_tokens),
                    api_key=os.getenv("OPENAI_API_KEY"),
                )
            logger.info(f"OpenAI model ({openai_model}) initialized successfully")
        except ImportError:
            logger.warning("langchain_openai not available")
            self.models["openai"] = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI model: {e}")
            self.models["openai"] = None
        
        # Google Gemini 모델 초기화
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.models["gemini"] = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=settings.gemini_temperature,
                max_output_tokens=int(settings.gemini_max_tokens),
                google_api_key=os.getenv("GEMINI_API_KEY")
            )
            logger.info("Gemini model initialized successfully")
        except ImportError:
            logger.warning("langchain_google_genai not available")
            self.models["gemini"] = None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.models["gemini"] = None
    
    def get_available_models(self) -> list:
        """사용 가능한 모델 목록을 반환합니다."""
        return [name for name, model in self.models.items() if model is not None]
    
    def _get_model(self, model_name: str) -> Runnable:
        """지정된 모델을 반환하거나 대체 모델을 찾습니다."""
        
        # 모델명을 provider로 매핑
        model_mapping = {
            # OpenAI 모델들
            "gpt-5": "openai",
            "gpt-5-mini": "openai",
            "gpt-4o": "openai",
            "gpt-4o-mini": "openai",
            
            # Gemini 모델들
            "gemini-2.5-pro": "gemini",
            "gemini-2.5-flash": "gemini", 
            "gemini-2.0-flash": "gemini",
        }
        
        # 먼저 정확한 모델명으로 매핑 시도
        provider = model_mapping.get(model_name)
        
        # 매핑되지 않은 경우 모델명에서 provider 추출 시도
        if not provider:
            if "gpt" in model_name.lower() or "openai" in model_name.lower():
                provider = "openai"
            elif "gemini" in model_name.lower():
                provider = "gemini"
            else:
                # 직접 provider명인 경우
                provider = model_name
        
        # 요청된 provider의 모델이 사용 가능한지 확인
        if provider in self.models and self.models[provider] is not None:
            return self.models[provider]
        
        # 대체 모델 우선순위 정의
        fallback_order = ["gemini", "openai"]
        
        logger.warning(f"Requested model '{model_name}' (provider: {provider}) not available, trying fallbacks...")
        
        for fallback in fallback_order:
            if fallback != provider and self.models.get(fallback) is not None:
                logger.info(f"Using fallback model: {fallback}")
                return self.models[fallback]
        
        raise RuntimeError(f"No available language models found. Requested: {model_name}")
    
    # LangChain Runnable 인터페이스 구현
    def invoke(self, input: Any, config: Optional[Dict] = None, **kwargs: Any) -> Any:
        """동기적으로 언어 모델을 호출합니다."""
        
        # config에서 모델명 추출
        model_name = None
        if config and isinstance(config, dict):
            model_name = config.get("model")
        if not model_name:
            model_name = kwargs.get("model", settings.default_llm_model)
        
        llm = self._get_model(model_name)
        
        try:
            # 입력 타입에 따라 처리
            if isinstance(input, str):
                response = llm.invoke([HumanMessage(content=input)], config=config, **kwargs)
            elif isinstance(input, dict):
                # dict 형태의 입력 (체인에서 오는 경우)
                if "text" in input:
                    response = llm.invoke([HumanMessage(content=input["text"])], config=config, **kwargs)
                else:
                    # 다른 키들을 조합해서 프롬프트 생성
                    prompt_text = str(input)
                    response = llm.invoke([HumanMessage(content=prompt_text)], config=config, **kwargs)
            elif isinstance(input, list):
                response = llm.invoke(input, config=config, **kwargs)
            else:
                response = llm.invoke(input, config=config, **kwargs)
            
            logger.debug(f"Successfully called {model_name} model")
            return response
            
        except Exception as e:
            logger.error(f"Error calling {model_name} model: {e}")
            raise
    
    async def ainvoke(self, input: Any, config: Optional[Dict] = None, **kwargs: Any) -> Any:
        """비동기적으로 언어 모델을 호출합니다."""
        
        # config에서 모델명 추출
        model_name = None
        if config and isinstance(config, dict):
            model_name = config.get("model")
        if not model_name:
            model_name = kwargs.get("model", settings.default_llm_model)
        
        llm = self._get_model(model_name)
        
        try:
            # 입력 타입에 따라 처리
            if isinstance(input, str):
                response = await llm.ainvoke([HumanMessage(content=input)], config=config, **kwargs)
            elif isinstance(input, dict):
                # dict 형태의 입력 (체인에서 오는 경우)
                if "text" in input:
                    response = await llm.ainvoke([HumanMessage(content=input["text"])], config=config, **kwargs)
                else:
                    # 다른 키들을 조합해서 프롬프트 생성
                    prompt_text = str(input)
                    response = await llm.ainvoke([HumanMessage(content=prompt_text)], config=config, **kwargs)
            elif isinstance(input, list):
                response = await llm.ainvoke(input, config=config, **kwargs)
            else:
                response = await llm.ainvoke(input, config=config, **kwargs)
            
            logger.debug(f"Successfully called {model_name} model")
            return response
            
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                logger.error(f"Event loop error in {model_name} model: {e}")
                # 이벤트 루프 에러의 경우 기본 응답 반환
                from langchain_core.messages import AIMessage
                return AIMessage(content="Default response due to event loop error")
            else:
                raise
        except Exception as e:
            logger.error(f"Error calling {model_name} model: {e}")
            raise
    
    def stream(self, input: Any, config: Optional[Dict] = None, **kwargs: Any):
        """스트리밍 방식으로 언어 모델을 호출합니다."""
        
        # config에서 모델명 추출
        model_name = None
        if config and isinstance(config, dict):
            model_name = config.get("model")
        if not model_name:
            model_name = kwargs.get("model", settings.default_llm_model)
        
        llm = self._get_model(model_name)
        
        try:
            if isinstance(input, str):
                return llm.stream([HumanMessage(content=input)], config=config, **kwargs)
            elif isinstance(input, dict):
                if "text" in input:
                    return llm.stream([HumanMessage(content=input["text"])], config=config, **kwargs)
                else:
                    prompt_text = str(input)
                    return llm.stream([HumanMessage(content=prompt_text)], config=config, **kwargs)
            elif isinstance(input, list):
                return llm.stream(input, config=config, **kwargs)
            else:
                return llm.stream(input, config=config, **kwargs)
                
        except Exception as e:
            logger.error(f"Error streaming from {model_name} model: {e}")
            raise
    
    async def astream(self, input: Any, config: Optional[Dict] = None, **kwargs: Any):
        """비동기 스트리밍 방식으로 언어 모델을 호출합니다."""
        
        # config에서 모델명 추출
        model_name = None
        if config and isinstance(config, dict):
            model_name = config.get("model")
        if not model_name:
            model_name = kwargs.get("model", settings.default_llm_model)
        
        llm = self._get_model(model_name)
        
        try:
            if isinstance(input, str):
                async for chunk in llm.astream([HumanMessage(content=input)], config=config, **kwargs):
                    yield chunk
            elif isinstance(input, dict):
                if "text" in input:
                    async for chunk in llm.astream([HumanMessage(content=input["text"])], config=config, **kwargs):
                        yield chunk
                else:
                    prompt_text = str(input)
                    async for chunk in llm.astream([HumanMessage(content=prompt_text)], config=config, **kwargs):
                        yield chunk
            elif isinstance(input, list):
                async for chunk in llm.astream(input, config=config, **kwargs):
                    yield chunk
            else:
                async for chunk in llm.astream(input, config=config, **kwargs):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error async streaming from {model_name} model: {e}")
            raise

class LanguageModel:
    """기존 호환성을 위한 래퍼 클래스"""
    
    def __init__(self, preferred: str = settings.default_llm_model):
        self.preferred = preferred
        logger.info(f"LanguageModel initialized with preferred model: {preferred}")
    
    async def ainvoke(self, prompt, **kwargs):
        """비동기 호출"""
        try:
            config = {"model": self.preferred}
            return await language_generator.ainvoke(prompt, config=config, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.ainvoke: {e}")
            raise
    
    def invoke(self, prompt, **kwargs):
        """동기 호출"""
        try:
            config = {"model": self.preferred}
            return language_generator.invoke(prompt, config=config, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.invoke: {e}")
            raise
    
    def stream(self, prompt, **kwargs):
        """스트리밍 호출"""
        try:
            config = {"model": self.preferred}
            return language_generator.stream(prompt, config=config, **kwargs)
        except Exception as e:
            logger.error(f"Error in LanguageModel.stream: {e}")
            raise
    
    async def astream(self, prompt, **kwargs):
        """비동기 스트리밍 호출"""
        try:
            config = {"model": self.preferred}
            async for chunk in language_generator.astream(prompt, config=config, **kwargs):
                yield chunk
        except Exception as e:
            logger.error(f"Error in LanguageModel.astream: {e}")
            raise


# 전역 인스턴스 생성
language_generator = UnifiedLanguageModel()

# 편의 함수들
async def call_llm(prompt: Union[str, list], model: str = None, **kwargs) -> Any:
    """언어 모델을 비동기적으로 호출하는 편의 함수"""
    config = {"model": model} if model else {}
    return await language_generator.ainvoke(prompt, config=config, **kwargs)

def call_llm_sync(prompt: Union[str, list], model: str = None, **kwargs) -> Any:
    """언어 모델을 동기적으로 호출하는 편의 함수"""
    config = {"model": model} if model else {}
    return language_generator.invoke(prompt, config=config, **kwargs)

def get_available_models() -> list:
    """사용 가능한 모델 목록을 반환하는 편의 함수"""
    return language_generator.get_available_models()
