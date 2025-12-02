import os
import json
from typing import Dict, Any, List, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.models.language.lyrics import SongLyricsRequest, SongLyricsResponse
from app.models.state import LyricsState, Page, PageText, get_valid_lyrics_state, serialize_for_json

from app.services.language.lyrics.generator import lyrics_generator
from app.services.language.lyrics.formatter import lyrics_formatter
from app.utils.logger.setup import setup_logger
from app.services.language.workflow.base_graph import BaseWorkflowGraph

# 환경 변수 로드
load_dotenv()
logger = setup_logger('lyrics_workflow', 'logs/services')


# LangGraph State 정의
class LyricsGraphState(TypedDict):
    """Lyrics 워크플로우 상태"""
    state: Dict[str, Any]
    model: str
    generator_result: Dict[str, Any]
    formatter_result: Dict[str, Any]
    final_result: Dict[str, Any]
    error: str

# LangGraph 노드 함수들
async def generate_lyrics_node(graph_state: LyricsGraphState) -> LyricsGraphState:
    """가사 생성 노드"""
    try:
        logger.info("가사 생성 노드 시작")

        model = graph_state["model"]
        state_data = graph_state["state"]

        # 가사 생성
        generator_result = await lyrics_generator({"state": state_data}, model=model)

        graph_state["generator_result"] = generator_result
        logger.info("가사 생성 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"가사 생성 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def format_lyrics_node(graph_state: LyricsGraphState) -> LyricsGraphState:
    """가사 포맷팅 노드"""
    try:
        logger.info("가사 포맷팅 노드 시작")

        model = graph_state["model"]
        generator_result = graph_state.get("generator_result", {})

        # 가사 포맷팅
        formatter_result = await lyrics_formatter(generator_result, model=model)

        graph_state["formatter_result"] = formatter_result
        logger.info("가사 포맷팅 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"가사 포맷팅 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def assemble_lyrics_results_node(graph_state: LyricsGraphState) -> LyricsGraphState:
    """가사 결과 조합 노드"""
    try:
        logger.info("가사 결과 조합 노드 시작")

        formatter_result = graph_state.get("formatter_result", {})

        # 최종 상태 가져오기
        final_state = get_valid_lyrics_state(formatter_result)

        # 결과 구성
        result = {
            "state": "Completed" if final_state.formatted_lyrics else "Incompleted",
            "songTitle": final_state.raw_lyrics.get("songTitle") if final_state.raw_lyrics else None,
            "lyrics": final_state.formatted_lyrics if isinstance(final_state.formatted_lyrics, list) else []
        }

        graph_state["final_result"] = result
        logger.info("가사 결과 조합 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"가사 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        graph_state["final_result"] = {
            "state": "Incompleted",
            "songTitle": None,
            "lyrics": []
        }
        return graph_state


# LangGraph 워크플로우 클래스
class LyricsWorkflowGraph(BaseWorkflowGraph):
    """Lyrics LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("lyrics")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(LyricsGraphState)

        # 노드 추가
        workflow.add_node("generate_lyrics", generate_lyrics_node)
        workflow.add_node("format_lyrics", format_lyrics_node)
        workflow.add_node("assemble_results", assemble_lyrics_results_node)

        # 엣지 정의
        workflow.set_entry_point("generate_lyrics")
        workflow.add_edge("generate_lyrics", "format_lyrics")
        workflow.add_edge("format_lyrics", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_lyrics_workflow(state: LyricsState, model: str) -> dict:
    """노래 가사 생성 워크플로우 실행 (LangGraph 기반)"""
    try:
        logger.info("LangGraph 기반 가사 생성 워크플로우 시작")

        # LangGraph 워크플로우 생성
        workflow_graph = LyricsWorkflowGraph()

        # 초기 상태 준비
        initial_state: LyricsGraphState = {
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
                "songTitle": None,
                "lyrics": []
            }

        return final_state.get("final_result", {
            "state": "Incompleted",
            "songTitle": None,
            "lyrics": []
        })

    except Exception as e:
        logger.error(f"가사 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "songTitle": None,
            "lyrics": []
        }

async def process_lyrics_workflow_wrapper(request_data) -> dict:
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
        
        # processedLlmText 처리 (CharacterContent 배열) - None 체크 추가
        processed_llm_text = request_dict.get("processedLlmText")
        if processed_llm_text is not None:
            for i, item in enumerate(processed_llm_text):
                if isinstance(item, dict) and "text" in item:
                    # CharacterContent 형태
                    text_content = item["text"]
                    texts = [PageText(text=text_content)]
                    pages.append(Page(pageKey=i+1, texts=texts))
                else:
                    logger.warning(f"Invalid processedLlmText item: {item}")
        
        # llmText 처리 (기존 형태와 호환성 유지) - None 체크 추가
        elif request_dict.get("llmText") is not None:
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
        
        else:
            raise ValueError("processedLlmText 또는 llmText 필드가 필요합니다.")
        
        if not pages:
            raise ValueError("처리할 텍스트 데이터가 없습니다.")
        
        # 상태 생성
        state = LyricsState(
            pages=pages,
            language=request_dict.get('language')
        )
        
        logger.info(f"Created LyricsState with {len(pages)} pages for language: {state.language}")
        
        # 워크플로우 실행 (model 전달)
        result = await process_lyrics_workflow(state, model=model)
        
        return result
    except Exception as e:
        logger.error(f"가사 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "songTitle": None,
            "lyrics": [],
            "error": str(e)
        }
