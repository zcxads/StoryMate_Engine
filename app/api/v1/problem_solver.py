"""
고도화된 문제 풀이 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from app.models.language.problem_solver import (
    ProblemSolverRequest,
    ProblemSolverResponse,
    SupportedProblemSolverModelsResponse,
    ProblemDetectionRequest,
    ProblemDetectionResponse,
    SUPPORTED_PROBLEM_SOLVER_MODELS
)
from app.services.language.problem_solver.solver import EnhancedProblemSolver
from app.services.language.problem_solver.crop import ProblemDetector
from app.core.config import settings
import time

router = APIRouter(prefix="/problem-solver")

# 고도화된 문제 풀이 서비스 인스턴스
problem_solver = EnhancedProblemSolver()
# OpenCV 기반 문제 검출기 인스턴스
problem_detector = ProblemDetector()

@router.get("/models", response_model=SupportedProblemSolverModelsResponse)
async def get_supported_models() -> SupportedProblemSolverModelsResponse:
    """
    고도화된 문제 풀이에서 지원되는 AI 모델 목록을 반환합니다.
    
    Returns:
        SupportedProblemSolverModelsResponse: 지원되는 모델 목록과 기본 모델 정보
    """
    return SupportedProblemSolverModelsResponse(
        supported_models=SUPPORTED_PROBLEM_SOLVER_MODELS,
        default_model=settings.llm_advanced_analysis_model,
        total_count=len(SUPPORTED_PROBLEM_SOLVER_MODELS)
    )

@router.post("/solve", response_model=ProblemSolverResponse)
async def solve_problem_enhanced(request: ProblemSolverRequest, raw_request: Request):
    """
    고도화된 문제 풀이 - 이미지 검증 후 단일 문제만 풀이
    
    - 정상적인 단일 문제: 답, 풀이과정, 핵심개념 제공
    - 비정상적인 문제 (여러 문제, 잘린 문제, 문제 없음, 저화질, 기울어짐, 가림, 낙서 등): "한 문제만 찍어서 업로드해주세요."
    """
    start_time = time.time()
    
    try:
        result = await problem_solver.solve_problem(request)
        
        # None 값을 제외한 JSON 응답 반환
        return JSONResponse(
            content=result.model_dump(exclude_none=True),
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"고도화된 문제 풀이 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/crop", response_model=ProblemDetectionResponse)
async def detect_problems_opencv(request: ProblemDetectionRequest):
    """
    Google Vision OCR 기반 문제 검출 및 분할 - 여러 문제가 포함된 이미지를 개별 문제로 분할

    - Google Vision OCR로 문제 번호 자동 검출
    - 적응형 크롭 시스템으로 문제별 크기 자동 조정
    - 컬럼 감지 및 텍스트 밀도 분석
    - 크롭된 문제 이미지 파일 저장 및 경로 반환
    """
    try:
        # Google Vision OCR 기반 문제 검출 및 분할
        result = await problem_detector.detect_and_segment_problems(
            image_base64=request.problem_image
        )
        
        if 'error' not in result:
            return JSONResponse(
                content=result,
                status_code=200
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"문제 검출에 실패했습니다: {result.get('error', '알 수 없는 오류')}"
            )
            
    except ValueError as e:
        # 이미지 처리 오류
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미지 처리 중 오류가 발생했습니다: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문제 검출 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health")
async def problem_solver_health_check():
    """고도화된 문제 풀이 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "Problem Solver (Enhanced)",
        "description": "고도화된 이미지 기반 문제 풀이 서비스 - 비정상 문제 감지 및 알림",
        "features": [
            "단일/다중 이미지 문제 풀이",
            "Google Vision OCR 기반 문제 번호 자동 검출",
            "적응형 크롭 시스템 (문제별 크기 자동 조정)",
            "컬럼 감지 및 가로 범위 자동 계산",
            "텍스트 밀도 분석 기반 세로 범위 계산",
            "안전 검증 시스템 (음수 height 방지)",
            "크롭된 문제 이미지 파일 저장 및 다운로드"
        ],
        "supported_models": SUPPORTED_PROBLEM_SOLVER_MODELS,
        "supported_languages": ["ko", "en", "ja", "zh"]
    }