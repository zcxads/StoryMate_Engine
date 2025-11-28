from fastapi import APIRouter, HTTPException, status
from app.models.language.question import (
    QuestionRequest, 
    QuestionResponse,
    SupportedModelsResponse,
    SUPPORTED_QUESTION_MODELS
)
from app.services.language.workflow.question import process_question_workflow_wrapper
from app.core.config import settings
import time

router = APIRouter(prefix="/question")

@router.get("/models", response_model=SupportedModelsResponse)
async def get_supported_models() -> SupportedModelsResponse:
    """
    추천 질문 생성에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedModelsResponse(
        supported_models=SUPPORTED_QUESTION_MODELS,
        default_model=settings.llm_text_processing_model,
        total_count=len(SUPPORTED_QUESTION_MODELS)
    )

@router.post("/", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest):
    """책 내용 기반 추천 질문 생성"""
    start_time = time.time()
    
    try:
        result = await process_question_workflow_wrapper(request)
        
        # 오류가 있는 경우 예외 발생
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "추천 질문 생성 중 알 수 없는 오류가 발생했습니다.")
            )
        
        # 실행 시간 추가 (워크플로우에서 계산된 시간 사용)
        execution_time = result.get("execution_time", f"{time.time() - start_time:.2f}s")
        
        return QuestionResponse(
            recommended_questions=result["recommended_questions"],
            model_used=result["model_used"],
            page_count=result["page_count"],
            execution_time=execution_time
        )
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"추천 질문 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def question_health_check():
    """추천 질문 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Question",
        "description": "책 내용 기반 추천 질문 생성 서비스"
    } 