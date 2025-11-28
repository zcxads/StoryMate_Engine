"""
고도화된 문제 풀이 서비스
"""

import time
from typing import List
from app.models.language.problem_solver import (
    ProblemSolverRequest,
    ProblemSolverResponse,
    ProblemValidationResult,
    ProblemType
)
from app.services.language.problem_solver.validator import ProblemImageValidator
from app.services.language.problem_solver.image_solver import solve_problem_from_image
from app.utils.logger.setup import setup_logger

logger = setup_logger('problem_solver', 'logs/services')

class EnhancedProblemSolver:
    """고도화된 문제 풀이 서비스 - 문제 풀이에만 집중"""

    def __init__(self):
        self.validator = ProblemImageValidator()

    async def solve_problem(self, request: ProblemSolverRequest) -> ProblemSolverResponse:
        """
        고도화된 문제 풀이 프로세스 (단일/다중 이미지 지원)

        Args:
            request: 문제 풀이 요청

        Returns:
            ProblemSolverResponse: 풀이 결과
        """
        start_time = time.time()

        try:
            # problem_images 리스트에서 이미지 가져오기
            images = request.problem_images
            logger.info(f"고도화된 문제 풀이 시작 - 이미지 수: {len(images)}, 모델: {request.model}, 언어: {request.language}")

            if len(images) == 1:
                # 단일 이미지: 기존 로직 사용
                return await self._solve_single_image(images[0], request, start_time)
            else:
                # 다중 이미지: 새로운 로직 사용
                return await self._solve_multiple_images(images, request, start_time)

        except Exception as e:
            logger.error(f"고도화된 문제 풀이 중 오류: {str(e)}", exc_info=True)
            execution_time = f"{time.time() - start_time:.2f}s"

            return ProblemSolverResponse(
                message="문제 풀이 중 오류가 발생했습니다. 이미지를 다시 확인해주세요."
            )

    async def _solve_single_image(self, image_base64: str, request: ProblemSolverRequest, start_time: float) -> ProblemSolverResponse:
        """단일 이미지 문제 풀이 (기존 로직)"""
        # 1단계: 문제 이미지 유효성 검증
        logger.info("단일 이미지 유효성 검증 시작...")
        validation_result = await self.validator.validate_problem_image(
            image_base64=image_base64,
            model=request.model
        )

        logger.info(f"검증 결과: {validation_result.problem_type.value}, 신뢰도: {validation_result.confidence}")

        # 2단계: 검증 결과에 따른 처리
        if validation_result.is_valid:
            # 정상적인 문제인 경우 - 문제 풀이 진행
            logger.info("정상 문제 감지, 풀이 시작...")

            solution_result = await solve_problem_from_image(
                image_base64=image_base64,
                model=request.model,
                language=request.language
            )

            execution_time = f"{time.time() - start_time:.2f}s"

            return ProblemSolverResponse(
                answer=solution_result.get("answer", ""),
                explanation=solution_result.get("solution", ""),
                concepts=solution_result.get("concepts", ""),
                execution_time=execution_time
            )
        else:
            # 비정상적인 문제인 경우 - 알림 메시지만 반환
            logger.info(f"비정상 문제 감지: {validation_result.problem_type.value}")

            execution_time = f"{time.time() - start_time:.2f}s"

            return ProblemSolverResponse(
                message="한 문제만 찍어서 업로드해주세요."
            )

    async def _solve_multiple_images(self, images: List[str], request: ProblemSolverRequest, start_time: float) -> ProblemSolverResponse:
        """다중 이미지 문제 풀이"""
        logger.info(f"다중 이미지 문제 풀이 시작 - 이미지 수: {len(images)}")

        try:
            # 1단계: 다중 이미지에서 독립적인 문제 여부 검증
            logger.info("다중 이미지 유효성 검증 시작...")
            validation_result = await self.validator.validate_multiple_images(
                images=images,
                model=request.model
            )

            logger.info(f"다중 이미지 검증 결과: {validation_result.problem_type.value}, 신뢰도: {validation_result.confidence}")

            # 2단계: 검증 결과에 따른 처리
            if validation_result.is_valid:
                # 단일 문제로 인식된 경우 - 문제 풀이 진행
                logger.info("단일 문제로 감지, 풀이 시작...")

                # solve_problem_from_image 함수에 다중 이미지를 전달
                solution_result = await solve_problem_from_image(
                    image_base64=images[0],  # 첫 번째 이미지를 주요 이미지로 사용
                    model=request.model,
                    language=request.language,
                    additional_images=images[1:] if len(images) > 1 else None  # 추가 이미지들
                )

                execution_time = f"{time.time() - start_time:.2f}s"

                return ProblemSolverResponse(
                    answer=solution_result.get("answer", ""),
                    explanation=solution_result.get("solution", ""),
                    concepts=solution_result.get("concepts", ""),
                    execution_time=execution_time
                )
            else:
                # 여러 독립적인 문제가 감지된 경우 - 재업로드 요청
                logger.info(f"여러 독립적인 문제 감지: {validation_result.details}")
                execution_time = f"{time.time() - start_time:.2f}s"

                return ProblemSolverResponse(
                    message="한 문제만 찍어서 업로드해주세요.",
                    execution_time=execution_time
                )

        except Exception as e:
            logger.error(f"다중 이미지 문제 풀이 중 오류: {str(e)}")
            execution_time = f"{time.time() - start_time:.2f}s"

            return ProblemSolverResponse(
                message="다중 이미지 문제 풀이 중 오류가 발생했습니다. 이미지를 다시 확인해주세요.",
                execution_time=execution_time
            )