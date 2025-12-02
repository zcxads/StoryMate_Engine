"""
LangGraph 기반 워크플로우 Base 클래스
"""
from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from app.utils.logger.setup import setup_logger

logger = setup_logger('base_graph', 'logs/workflow')


class BaseWorkflowState(TypedDict, total=False):
    """워크플로우 기본 상태 클래스"""
    model: str
    status: str
    error: Optional[str]
    execution_time: Optional[str]


class BaseWorkflowGraph:
    """LangGraph 기반 워크플로우 Base 클래스"""

    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(f'{name}_graph', 'logs/workflow')
        self.graph = None

    def build_graph(self) -> StateGraph:
        """
        워크플로우 그래프를 구성합니다.
        """
        raise NotImplementedError("Subclass must implement build_graph method")

    def compile_graph(self):
        """그래프를 컴파일합니다."""
        if self.graph is None:
            self.graph = self.build_graph()
        return self.graph.compile()

    async def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        워크플로우를 실행합니다.

        Args:
            initial_state: 초기 상태

        Returns:
            최종 상태
        """
        try:
            self.logger.info(f"{self.name} 워크플로우 실행 시작")
            compiled_graph = self.compile_graph()

            # 그래프 실행
            final_state = await compiled_graph.ainvoke(initial_state)

            self.logger.info(f"{self.name} 워크플로우 실행 완료")
            return final_state

        except Exception as e:
            self.logger.error(f"{self.name} 워크플로우 실행 중 오류: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
