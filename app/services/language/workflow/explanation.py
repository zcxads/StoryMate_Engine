"""
이미지 기반 문제 해결 워크플로우 래퍼
"""

import time
import re
from typing import Dict, Any, Union, TypedDict

from langgraph.graph import StateGraph, END

from app.models.language.explanation import ExplanationRequest
from app.services.language.explanation.solver import solve_problem_from_image
from app.utils.logger.setup import setup_logger
from app.core.config import settings
from app.services.language.workflow.base_graph import BaseWorkflowGraph

# 로거 설정
logger = setup_logger('explanation_workflow', 'logs/workflow')


# LangGraph State 정의
class ExplanationGraphState(TypedDict):
    """Explanation 워크플로우 상태"""
    model: str
    problem_image: str
    language: str
    problem_result: Dict[str, Any]
    genre_enum: Any
    final_result: Dict[str, Any]
    error: str
    start_time: float

# LangGraph 노드 함수들
async def solve_problem_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """문제 해결 노드"""
    try:
        logger.info("문제 해결 노드 시작")

        model = graph_state["model"]
        problem_image = graph_state["problem_image"]
        language = graph_state["language"]

        # 문제 해결
        problem_result = await solve_problem_from_image(problem_image, model, language)

        graph_state["problem_result"] = problem_result
        logger.info("문제 해결 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"문제 해결 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def detect_genre_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """장르 감지 노드"""
    try:
        logger.info("장르 감지 노드 시작")

        problem_result = graph_state.get("problem_result", {})
        model = graph_state["model"]
        language = graph_state["language"]

        # 장르 자동 감지
        genre_enum = None
        try:
            from app.services.language.content_category.analyzer import ContentCategoryAnalyzer
            from app.models.language.content_category import ContentCategoryRequest

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

        graph_state["genre_enum"] = genre_enum
        logger.info("장르 감지 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"장르 감지 노드 오류: {str(e)}", exc_info=True)
        # 장르 감지 실패는 치명적이지 않으므로 계속 진행
        graph_state["genre_enum"] = None
        return graph_state


async def assemble_explanation_results_node(graph_state: ExplanationGraphState) -> ExplanationGraphState:
    """문제 해결 결과 조합 노드"""
    try:
        logger.info("문제 해결 결과 조합 노드 시작")

        problem_result = graph_state.get("problem_result", {})
        genre_enum = graph_state.get("genre_enum")
        model = graph_state["model"]
        start_time = graph_state["start_time"]

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # 최종 응답 구성
        final_result = problem_result.copy()
        final_result.update({
            "genre": genre_enum,
            "model_used": model,
            "execution_time": execution_time,
            "status": "success" if not graph_state.get("error") else "error"
        })

        if graph_state.get("error"):
            final_result["error"] = graph_state["error"]

        graph_state["final_result"] = final_result
        logger.info(f"문제 해결 결과 조합 완료 - 실행시간: {execution_time}")
        return graph_state

    except Exception as e:
        logger.error(f"문제 해결 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


# LangGraph 워크플로우 클래스
class ExplanationWorkflowGraph(BaseWorkflowGraph):
    """Explanation LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("explanation")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(ExplanationGraphState)

        # 노드 추가
        workflow.add_node("solve_problem", solve_problem_node)
        workflow.add_node("detect_genre", detect_genre_node)
        workflow.add_node("assemble_results", assemble_explanation_results_node)

        # 엣지 정의
        workflow.set_entry_point("solve_problem")
        workflow.add_edge("solve_problem", "detect_genre")
        workflow.add_edge("detect_genre", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_explanation_workflow_wrapper(request: Union[ExplanationRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 이미지 기반 문제를 해결하고 결과를 반환하는 wrapper 함수. (LangGraph 기반)

    Args:
        request: ExplanationRequest 객체 또는 딕셔너리 형태의 요청 데이터

    Returns:
        Dict[str, Any]: 문제 해결 결과를 포함한 응답 데이터
    """
    start_time = time.time()

    try:
        logger.info("LangGraph 기반 문제 해결 워크플로우 처리 시작")

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

        # LangGraph 워크플로우 생성
        workflow_graph = ExplanationWorkflowGraph()

        # 초기 상태 준비
        initial_state: ExplanationGraphState = {
            "model": model,
            "problem_image": problem_image,
            "language": language,
            "problem_result": {},
            "genre_enum": None,
            "final_result": {},
            "error": "",
            "start_time": start_time
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 오류가 있으면 예외 발생
        if final_state.get("error"):
            raise Exception(final_state["error"])

        logger.info("문제 해결 워크플로우 처리 완료")
        return final_state.get("final_result", {})

    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"문제 해결 워크플로우 실패: {str(e)}"
        logger.info(error_msg)

        # Exception을 그대로 전파하여 API에서 detail로 처리
        raise e
