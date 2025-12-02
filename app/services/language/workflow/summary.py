"""
책 내용 요약 워크플로우 래퍼
"""

import time
from typing import Dict, Any, Union, List, TypedDict
from langgraph.graph import StateGraph, END

from app.models.language.summary import SummaryRequest
from app.services.language.summary.generator import generate_book_summary
from app.utils.logger.setup import setup_logger
from app.services.language.workflow.base_graph import BaseWorkflowGraph

# 로거 설정
logger = setup_logger('summary_workflow', 'logs/workflow')


# LangGraph State 정의
class SummaryGraphState(TypedDict):
    """Summary 워크플로우 상태"""
    model: str
    pages_data: List[Dict[str, Any]]
    summary: str
    final_result: Dict[str, Any]
    error: str
    start_time: float

# LangGraph 노드 함수들
async def generate_summary_node(graph_state: SummaryGraphState) -> SummaryGraphState:
    """요약 생성 노드"""
    try:
        logger.info("요약 생성 노드 시작")

        model = graph_state["model"]
        pages_data = graph_state["pages_data"]

        # 요약 생성
        summary = await generate_book_summary(pages_data, model)

        graph_state["summary"] = summary
        logger.info("요약 생성 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"요약 생성 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        graph_state["summary"] = ""
        return graph_state


async def assemble_summary_results_node(graph_state: SummaryGraphState) -> SummaryGraphState:
    """요약 결과 조합 노드"""
    try:
        logger.info("요약 결과 조합 노드 시작")

        summary = graph_state.get("summary", "")
        model = graph_state["model"]
        pages_data = graph_state["pages_data"]
        start_time = graph_state["start_time"]

        # 실행 시간 계산
        execution_time = f"{time.time() - start_time:.2f}s"

        # 결과 구성
        result = {
            "summary": summary,
            "model_used": model,
            "page_count": len(pages_data),
            "execution_time": execution_time,
            "status": "success" if not graph_state.get("error") else "error"
        }

        if graph_state.get("error"):
            result["error"] = graph_state["error"]

        graph_state["final_result"] = result
        logger.info(f"요약 결과 조합 완료 - 실행시간: {execution_time}")
        return graph_state

    except Exception as e:
        logger.error(f"요약 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


# LangGraph 워크플로우 클래스
class SummaryWorkflowGraph(BaseWorkflowGraph):
    """Summary LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("summary")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(SummaryGraphState)

        # 노드 추가
        workflow.add_node("generate_summary", generate_summary_node)
        workflow.add_node("assemble_results", assemble_summary_results_node)

        # 엣지 정의
        workflow.set_entry_point("generate_summary")
        workflow.add_edge("generate_summary", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_summary_workflow_wrapper(request: Union[SummaryRequest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    API 요청을 입력받아 책 내용 요약을 생성하고 결과를 반환하는 wrapper 함수. (LangGraph 기반)

    Args:
        request: SummaryRequest 객체 또는 딕셔너리 형태의 요청 데이터

    Returns:
        Dict[str, Any]: 요약 결과를 포함한 응답 데이터
    """
    start_time = time.time()

    try:
        logger.info("LangGraph 기반 책 요약 워크플로우 처리 시작")

        # 요청 데이터 추출
        if isinstance(request, dict):
            model = request.get("model")
            pages = request.get("pages", [])
        else:
            model = getattr(request, "model")
            pages = getattr(request, "pages", [])
            # Pydantic 모델인 경우 dict로 변환
            if hasattr(request, 'dict'):
                request_dict = request.dict()
                pages = request_dict.get("pages", [])
                pages = [page for page in request_dict.get("pages", [])]

        if not pages:
            raise ValueError("요약할 페이지 데이터가 없습니다.")

        logger.info(f"요약 생성 시작 - 모델: {model}, 페이지 수: {len(pages)}")

        # 페이지 데이터를 딕셔너리 형태로 변환
        pages_data = []
        for page in pages:
            if isinstance(page, dict):
                pages_data.append(page)
            else:
                # Pydantic 모델인 경우
                pages_data.append({
                    "pageKey": getattr(page, "pageKey", 0),
                    "text": getattr(page, "text", "")
                })

        # LangGraph 워크플로우 생성
        workflow_graph = SummaryWorkflowGraph()

        # 초기 상태 준비
        initial_state: SummaryGraphState = {
            "model": model,
            "pages_data": pages_data,
            "summary": "",
            "final_result": {},
            "error": "",
            "start_time": start_time
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 결과 반환
        return final_state.get("final_result", {
            "summary": "",
            "model_used": model,
            "page_count": len(pages_data),
            "execution_time": f"{time.time() - start_time:.2f}s",
            "status": "error",
            "error": final_state.get("error", "알 수 없는 오류")
        })

    except Exception as e:
        execution_time = f"{time.time() - start_time:.2f}s"
        error_msg = f"책 요약 워크플로우 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 오류 응답 구성
        return {
            "summary": "",
            "model_used": model if 'model' in locals() else "unknown",
            "page_count": len(pages) if 'pages' in locals() else 0,
            "execution_time": execution_time,
            "status": "error",
            "error": str(e)
        } 