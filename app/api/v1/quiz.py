from fastapi import APIRouter, HTTPException, status, Request
from app.models.language.quiz import (
    QuizRequest,
    QuizResponse,
    SupportedModelsResponse,
    SupportedProblemTypesResponse,
    SUPPORTED_QUIZ_MODELS,
    PROBLEM_TYPE_DESCRIPTIONS
)
from app.utils.logger.setup import setup_logger
from app.services.language.workflow.quiz import process_quiz_workflow_wrapper
from app.core.config import settings
import time

router = APIRouter(prefix="/quiz")
logger = setup_logger('quiz')

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    퀴즈 생성에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_QUIZ_MODELS,
        default_model=settings.default_llm_model,
        total_count=len(SUPPORTED_QUIZ_MODELS)
    )

@router.get("/problem-types", response_model=SupportedProblemTypesResponse)
async def get_supported_problem_types() -> SupportedProblemTypesResponse:
    """
    퀴즈 생성에서 지원되는 문제 유형 목록을 반환합니다.
    
    Returns:
        SupportedProblemTypesResponse: 지원되는 문제 유형 목록
    """
    return SupportedProblemTypesResponse(
        problem_types=PROBLEM_TYPE_DESCRIPTIONS,
        total_count=len(PROBLEM_TYPE_DESCRIPTIONS)
    )

@router.post("/", response_model=QuizResponse)
async def process_quiz(request: QuizRequest):
    """텍스트 기반 퀴즈 생성"""
    start_time = time.time()

    try:
        result = await process_quiz_workflow_wrapper(request)

        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"퀴즈 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def quiz_health_check():
    """퀴즈 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Quiz",
        "description": "퀴즈 생성 서비스"
    }
