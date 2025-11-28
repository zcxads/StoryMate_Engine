"""
이미지 기반 문제 해결 워크플로우 래퍼
"""

import time
import re
from typing import Dict, Any, Union

from app.models.language.explanation import ExplanationRequest
from app.services.language.explanation.solver import solve_problem_from_image
from app.utils.logger.setup import setup_logger
from app.core.config import settings

# 로거 설정
logger = setup_logger('explanation_workflow', 'logs/workflow')

async def process_explanation_workflow_wrapper(request: Union[ExplanationRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 이미지 기반 문제를 해결하고 결과를 반환하는 wrapper 함수.
    
    Args:
        request: ExplanationRequest 객체 또는 딕셔너리 형태의 요청 데이터
    
    Returns:
        Dict[str, Any]: 문제 해결 결과를 포함한 응답 데이터
    """
    start_time = time.time()

    try:
        logger.info("문제 해결 워크플로우 처리 시작")

        # 요청 데이터 추출
        if isinstance(request, dict):
            model = request.get("model")
            problem_image = request.get("problem")
            language = request.get("language")
        else:
            model = getattr(request, "model")
            problem_image = getattr(request, "problem")
            language = getattr(request, "language")
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(request, 'model_dump'):
                request_dict = request.model_dump()
                model = request_dict.get("model")
                problem_image = request_dict.get("problem")
                language = request_dict.get("language")
            elif hasattr(request, 'dict'):
                request_dict = request.dict()
                model = request_dict.get("model")
                problem_image = request_dict.get("problem")
                language = request_dict.get("language")

        if not problem_image:
            raise ValueError("문제 이미지 데이터가 없습니다.")

        logger.info(f"문제 해결 시작 - 모델: {model}, 언어: {language}")

        # 문제 해결 (개선된 solver 사용)
        problem_result = await solve_problem_from_image(problem_image, model, language)

        # 장르 자동 감지
        genre_enum = None
        try:
            from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
            from app.models.language.content_category import ContentCategoryRequest, TextItem

            # 문제와 해설 텍스트 결합하여 장르 분석
            combined_text = f"{problem_result.get('answer')} {problem_result.get('solution')} {problem_result.get('concepts')}"

            analyzer = ContentCategoryAnalyzer()
            category_request = ContentCategoryRequest(
                llmText=[{"pageKey": 0, "texts": [{"text": combined_text}]}],
                model=model,
                language=language
            )

            category_result = await analyzer.analyze_content(category_request)
            genre_enum = category_result.genre
            logger.info(f"Auto-detected genre: {genre_enum.value}")
        except Exception as e:
            logger.warning(f"Failed to auto-detect genre: {str(e)}")

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # 최종 응답 구성 - 정리된 결과 + 메타데이터
        final_result = problem_result.copy()
        final_result.update({
            "genre": genre_enum,
            "model_used": model,
            "execution_time": execution_time,
            "status": "success"
        })

        logger.info(f"문제 해결 워크플로우 처리 완료 - 실행시간: {execution_time}")
        return final_result

    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"문제 해결 워크플로우 실패: {str(e)}"
        logger.info(error_msg)

        # Exception을 그대로 전파하여 API에서 detail로 처리
        raise e
