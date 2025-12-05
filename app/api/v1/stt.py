from fastapi import APIRouter, HTTPException, status, Request
from app.models.voice.stt import (
    STTRequest,
    STTResponse,
    STTErrorResponse,
    SupportedSTTLanguage,
    SupportedSTTModelsResponse,
    SUPPORTED_STT_MODELS
)
from app.core.config import settings
from app.services.voice.stt.feature_matcher import match_text_to_feature
from app.utils.logger.setup import setup_logger

router = APIRouter(prefix="/stt")
@router.get("/models", response_model=SupportedSTTModelsResponse)
async def get_supported_models() -> SupportedSTTModelsResponse:
    """지원되는 STT 모델 목록을 반환합니다."""
    return SupportedSTTModelsResponse(
        supported_models=SUPPORTED_STT_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_STT_MODELS)
    )

logger = setup_logger('stt_api')

@router.get("/languages")
async def get_supported_languages():
    """
    지원되는 STT 언어 목록을 반환합니다.

    Returns:
        Dict: 지원되는 언어 목록
    """
    return {
        "supported_languages": [
            {"code": lang.value, "name": _get_language_name(lang.value)}
            for lang in SupportedSTTLanguage
        ],
        "default_language": "auto"
    }


@router.post("/transcribe-with-matching", response_model=STTResponse, responses={
    422: {"model": STTErrorResponse, "description": "유효성 검사 오류"},
    500: {"model": STTErrorResponse, "description": "서버 내부 오류"}
})
async def transcribe_audio_with_matching(
    stt_request: STTRequest
):
    """
    텍스트를 받아 앱 기능과 매칭합니다.

    Args:
        stt_request: STT 요청 (text 필드)

    Returns:
        STTResponse: 기능 매칭 결과

    Raises:
        422: 유효성 검사 오류 (빈 텍스트, 잘못된 입력 등)
        500: 서버 내부 오류
    """
    try:
        # 입력 유효성 검증
        if not stt_request.text or not stt_request.text.strip():
            logger.warning("빈 텍스트 요청 수신")
            raise HTTPException(
                status_code=422,
                detail="텍스트를 입력해주세요."
            )

        # 텍스트 길이 검증 (최대 1000자)
        if len(stt_request.text) > 1000:
            logger.warning(f"텍스트 길이 초과: {len(stt_request.text)}자")
            raise HTTPException(
                status_code=422,
                detail="텍스트는 최대 1000자까지 입력 가능합니다."
            )

        logger.info(f"STT 매칭 요청 수신 - 텍스트: {stt_request.text}")

        # 기능 매칭 (텍스트에서 자동으로 언어 감지)
        matching_result = await match_text_to_feature(stt_request.text)

        logger.info(f"STT 매칭 완료 - matched: {matching_result.get('matched')}, component: {matching_result.get('component')}")

        # 매칭 실패 시 500 에러 반환
        if not matching_result.get('matched'):
            logger.warning(f"기능 매칭 실패 - 텍스트: {stt_request.text}, 점수: {matching_result.get('score')}")
            raise HTTPException(
                status_code=500,
                detail="해당하는 기능을 찾을 수 없습니다."
            )

        # 성공 응답
        return STTResponse(**matching_result)

    except Exception as e:
        # 서버 내부 오류 (500)
        logger.error(f"STT 매칭 처리 중 서버 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/health")
async def stt_health_check():
    """STT 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Speech-to-Text Feature Matching",
        "description": "OpenAI GPT 기반 기능 매칭 서비스",
        "model": "gpt-4o",
        "features": [
            "텍스트 기반 기능 매칭",
            "다국어 지원",
            "유사도 점수 제공"
        ]
    }

def _get_language_name(language_code: str) -> str:
    """언어 코드를 언어 이름으로 변환"""
    language_names = {
        "auto": "자동 감지",
        "ko": "한국어",
        "en": "영어",
        "ja": "일본어",
        "zh": "중국어",
    }
    return language_names.get(language_code, language_code)