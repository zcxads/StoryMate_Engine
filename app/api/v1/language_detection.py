from fastapi import APIRouter, HTTPException, status
import re
from app.models.language.language_detection import (
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    SupportedLanguageDetectionModelsResponse,
    SUPPORTED_LANGUAGE_DETECTION_MODELS
)
from app.services.language.language_detection.detector import detect_language_with_ai
from app.prompts.language.language_detection.detector import get_supported_languages
from app.config import settings
import time

router = APIRouter(prefix="/language-detection")

@router.get("/models", response_model=SupportedLanguageDetectionModelsResponse)
async def get_supported_models() -> SupportedLanguageDetectionModelsResponse:
    """
    언어 감지에서 지원되는 AI 모델 목록을 반환합니다.
    """
    return SupportedLanguageDetectionModelsResponse(
        supported_models=SUPPORTED_LANGUAGE_DETECTION_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_LANGUAGE_DETECTION_MODELS)
    )

@router.post("/", response_model=LanguageDetectionResponse)
async def process_language_detection(request: LanguageDetectionRequest):
    """AI 기반 텍스트 언어 감지 (Gemini 2.0 Flash)"""
    start_time = time.time()
    
    try:
        # 숫자만 포함된 입력(문자 없음)은 언어를 특정할 수 없으므로 500 반환
        input_text = request.texts or ""
        has_letter = re.search(r'[^\W\d_]', input_text, re.UNICODE) is not None
        has_digit = re.search(r'\d', input_text) is not None
        if has_digit and not has_letter:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="숫자만 포함된 입력은 언어를 특정할 수 없어 처리할 수 없습니다."
            )

        # 언어 문자가 전혀 없는 입력(예: "/\\-_=+*" 등 기호만)도 언어를 특정할 수 없으므로 500 반환
        has_language_script = re.search(r'[a-zA-Z\uac00-\ud7a3\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', input_text) is not None
        if not has_language_script:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="언어를 특정할 수 없는 문자만 포함되어 처리할 수 없습니다."
            )

        # 중앙 설정에서 모델 사용
        result = await detect_language_with_ai(request.texts, model_name=settings.default_llm_model)
        
        # 언어 이름 매핑
        supported_languages = get_supported_languages()
        detected_language_name = supported_languages.get(result["primary_language"], result["primary_language"])
        
        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        
        # 감지 실패 시 500 에러 반환 (unknown 또는 내부 오류 플래그 존재 시)
        if result.get("primary_language") in [None, "", "unknown"] or result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"언어를 감지할 수 없습니다. 입력을 확인해주세요."
            )

        # 기존 응답 형식에 맞춰 변환
        response_data = {
            "detected_language": result["primary_language"]
        }
        
        return LanguageDetectionResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"언어 감지 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages_list():
    """지원하는 언어 목록 조회"""
    supported_languages = get_supported_languages()
    
    return {
        "supported_languages": [
            {"code": code, "name": name}
            for code, name in supported_languages.items()
        ],
        "total_count": len(supported_languages),
        "model": settings.default_llm_model
    }

@router.get("/health")
async def language_detection_health_check():
    """언어 감지 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Language Detection",
        "description": "AI 기반 텍스트 언어 감지 서비스",
        "method": "ai",
        "model": settings.default_llm_model,
        "supported_languages": ["Korean", "Japanese", "English", "Chinese (General)", "Chinese (Simplified)", "Chinese (Traditional)"]
    } 