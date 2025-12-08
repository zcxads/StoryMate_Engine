from fastapi import APIRouter, HTTPException, status, Request
from app.models.language.explanation import (
    ExplanationRequest,
    ExplanationResponse,
    SimilarQuizRequest,
    SimilarQuizResponse,
    SupportedModelsResponse,
    SUPPORTED_EXPLANATION_MODELS
)
from app.services.language.workflow.explanation import (
    process_explanation_workflow_wrapper,
    process_similar_quiz_workflow_wrapper
)
from app.config import settings
import time

router = APIRouter(prefix="/explanation")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    문제 해설에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_EXPLANATION_MODELS,
        default_model=settings.llm_for_explanation,
        total_count=len(SUPPORTED_EXPLANATION_MODELS)
    )

@router.post("/", response_model=ExplanationResponse)
async def solve_problem(request: ExplanationRequest):
    """문제 이미지를 분석하여 해답과 해설을 제공"""
    start_time = time.time()

    try:
        result = await process_explanation_workflow_wrapper(request)

        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/similar", response_model=SimilarQuizResponse)
async def generate_similar_quiz(request: SimilarQuizRequest):
    """이미지 기반 유사 문제 생성"""
    start_time = time.time()

    try:
        result = await process_similar_quiz_workflow_wrapper(request)

        # 실행 시간 추가
        execution_time = f"{time.time() - start_time:.2f}s"
        result["execution_time"] = execution_time

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def explanation_health_check():
    """문제 해결 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Explanation",
        "description": "이미지 기반 문제 해결 서비스"
    } 