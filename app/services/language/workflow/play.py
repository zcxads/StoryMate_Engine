import os
import json
from typing import Dict, Any, TypedDict
from app.utils.logger.setup import setup_logger
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.models.language.play import PlayRequest
from app.models.state import Page, PageText, serialize_for_json, PlayState, get_valid_play_state
from app.services.language.play.generator import play_generator
from app.services.language.play.formatter import play_formatter
from app.services.language.workflow.base_graph import BaseWorkflowGraph

load_dotenv()
logger = setup_logger('workflow_play')


# LangGraph State 정의
class PlayGraphState(TypedDict):
    """Play 워크플로우 상태"""
    state: Dict[str, Any]
    model: str
    generator_result: Dict[str, Any]
    formatter_result: Dict[str, Any]
    final_result: Dict[str, Any]
    error: str


# LangGraph 노드 함수들
async def generate_play_node(graph_state: PlayGraphState) -> PlayGraphState:
    """연극 대사 생성 노드"""
    try:
        logger.info("연극 대사 생성 노드 시작")

        model = graph_state["model"]
        state_data = graph_state["state"]

        # 연극 대사 생성
        generator_result = await play_generator({"state": state_data}, model=model)

        graph_state["generator_result"] = generator_result
        logger.info("연극 대사 생성 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"연극 대사 생성 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def format_play_node(graph_state: PlayGraphState) -> PlayGraphState:
    """연극 대사 포맷팅 노드"""
    try:
        logger.info("연극 대사 포맷팅 노드 시작")

        model = graph_state["model"]
        generator_result = graph_state.get("generator_result", {})

        # 연극 대사 포맷팅
        formatter_result = await play_formatter(generator_result, model=model)

        graph_state["formatter_result"] = formatter_result
        logger.info("연극 대사 포맷팅 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"연극 대사 포맷팅 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def assemble_play_results_node(graph_state: PlayGraphState) -> PlayGraphState:
    """연극 대사 결과 조합 노드"""
    try:
        logger.info("연극 대사 결과 조합 노드 시작")

        formatter_result = graph_state.get("formatter_result", {})

        # 최종 상태 가져오기
        final_state = get_valid_play_state(formatter_result)

        # 결과 구성
        result = {
            "state": "Completed" if final_state.formatted_play else "Incompleted",
            "message": "Completion of the creation of theatrical lines" if final_state.formatted_play else "Failure to generate theatrical lines",
            "playTitle": final_state.raw_play.get("playTitle") if final_state.raw_play else None,
            "script": final_state.formatted_play if isinstance(final_state.formatted_play, list) else []
        }

        graph_state["final_result"] = result
        logger.info("연극 대사 결과 조합 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"연극 대사 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        graph_state["final_result"] = {
            "state": "Incompleted",
            "message": "Failure to generate theatrical lines",
            "playTitle": None,
            "script": []
        }
        return graph_state


# LangGraph 워크플로우 클래스
class PlayWorkflowGraph(BaseWorkflowGraph):
    """Play LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("play")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(PlayGraphState)

        # 노드 추가
        workflow.add_node("generate_play", generate_play_node)
        workflow.add_node("format_play", format_play_node)
        workflow.add_node("assemble_results", assemble_play_results_node)

        # 엣지 정의
        workflow.set_entry_point("generate_play")
        workflow.add_edge("generate_play", "format_play")
        workflow.add_edge("format_play", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_play_workflow(state, model) -> dict:
    """연극 대사 생성 워크플로우 실행 (LangGraph 기반)"""
    try:
        logger.info("LangGraph 기반 연극 대사 생성 워크플로우 시작")

        # LangGraph 워크플로우 생성
        workflow_graph = PlayWorkflowGraph()

        # 초기 상태 준비
        initial_state: PlayGraphState = {
            "state": state.model_dump(),
            "model": model,
            "generator_result": {},
            "formatter_result": {},
            "final_result": {},
            "error": ""
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 결과 반환
        if final_state.get("error"):
            logger.error(f"워크플로우 실행 중 오류 발생: {final_state['error']}")
            return {
                "state": "Incompleted",
                "message": "Failure to generate theatrical lines",
                "playTitle": None,
                "script": []
            }

        return final_state.get("final_result", {
            "state": "Incompleted",
            "message": "Failure to generate theatrical lines",
            "playTitle": None,
            "script": []
        })

    except Exception as e:
        logger.error(f"연극 대사 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "message": str(e),
            "playTitle": None,
            "script": []
        }


async def process_play_workflow_wrapper(request_data) -> dict:
    """API 요청을 처리하는 wrapper 함수"""
    try:
        # request_data가 Pydantic 모델인 경우 dict로 변환
        if hasattr(request_data, 'model_dump'):
            request_dict = request_data.model_dump()
        elif hasattr(request_data, 'dict'):
            request_dict = request_data.dict()
        else:
            request_dict = request_data
        
        # model 필드 추출
        model = request_dict.get("model")
        
        pages = []
        
        # llmText 처리 (기존 형태와 호환성 유지) - None 체크 추가
        if request_dict.get("llmText") is not None:
            llm_text = request_dict["llmText"]
            for page in llm_text:
                if isinstance(page, dict) and "texts" in page:
                    texts = []
                    for text_item in page["texts"]:
                        if isinstance(text_item, dict) and "text" in text_item:
                            texts.append(PageText(text=text_item["text"]))
                        else:
                            logger.warning(f"Invalid text item: {text_item}")
                    
                    page_key = page.get("pageKey", len(pages) + 1)
                    pages.append(Page(pageKey=page_key, texts=texts))
                else:
                    logger.warning(f"Invalid llmText page: {page}")
                    
        
            state = PlayState(
                pages=pages,
                language=request_dict.get('language', '')
            )
        
            response = await process_play_workflow(state, model)
            
            if response.get("error"):
                return {
                    "state": "Incompleted",
                    "message": response.get("error"),
                    "playTitle": None,
                    "script": [],
                }
            else:
                return {
                    "state": "Completed",
                    "message": "연극 대사 생성 완료",
                    "playTitle": response.get("playTitle"),
                    "script": response.get("script"),
                }
                    
        else:
            return {
                "state": "Incompleted",
                "message": "llmText가 전달되지 않았습니다.",
                "playTitle": None,
                "script": [],
            }
            
    except Exception as e:
        logger.error(f"연극 대사 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "message": str(e),
            "playTitle": None,
            "script": []
        }