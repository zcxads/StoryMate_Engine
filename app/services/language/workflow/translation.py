import json
import asyncio
from typing import Dict, Any, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.services.language.translation.translator import translation_agent
from app.utils.logger.setup import setup_logger
from app.models.language.translation import TranslationRequest
from app.services.language.workflow.base_graph import BaseWorkflowGraph

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger('translation_workflow', 'logs/translation')


# LangGraph State 정의
class TranslationGraphState(TypedDict):
    """Translation 워크플로우 상태"""
    state: Dict[str, Any]
    model: str
    translation_result: Dict[str, Any]
    final_result: Dict[str, Any]
    error: str

# LangGraph 노드 함수들
async def translate_node(graph_state: TranslationGraphState) -> TranslationGraphState:
    """번역 노드"""
    try:
        logger.info("번역 노드 시작")

        model = graph_state["model"]
        state_data = graph_state["state"]

        # 원본 상태 로깅
        logger.info("Original state llmText length: {}".format(len(state_data.get('llmText', []))))
        if state_data.get('llmText', []) and len(state_data.get('llmText', [])) > 0:
            sample_original = state_data['llmText'][0]
            if "texts" in sample_original and len(sample_original["texts"]) > 0:
                logger.info("Original sample text: {}".format(sample_original['texts'][0]))

        # 번역 실행
        translation_result = await translation_agent({"state": state_data}, model=model)

        graph_state["translation_result"] = translation_result
        logger.info("번역 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"번역 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        return graph_state


async def assemble_translation_results_node(graph_state: TranslationGraphState) -> TranslationGraphState:
    """번역 결과 조합 노드"""
    try:
        logger.info("번역 결과 조합 노드 시작")

        translation_result = graph_state.get("translation_result", {})
        state_data = graph_state["state"]

        # 최종 상태 가져오기 및 확인
        final_data = translation_result.get("state", {})
        logger.info("Final state keys: {}".format(final_data.keys() if isinstance(final_data, dict) else 'Not a dict'))

        # 중요: 번역된 llmText 확인 및 로깅
        llm_text = final_data.get("llmText", [])
        logger.info("Final llmText length: {}".format(len(llm_text)))
        if llm_text and len(llm_text) > 0:
            sample_page = llm_text[0]
            if "texts" in sample_page and len(sample_page["texts"]) > 0:
                logger.info("Sample translated text: {}".format(sample_page['texts'][0]['text']))

        # 기본 응답 구성 - 번역 표시자 추가
        result = {
            "state": "Completed" if not final_data.get("error") and not graph_state.get("error") else "Incompleted",
            "llmText": llm_text,
            "target": final_data.get("target"),
            "translated": True  # 번역 완료 표시
        }

        # 추가 로깅
        logger.info("Returning response with {} llmText items".format(len(llm_text)))
        if llm_text and len(llm_text) > 0 and "texts" in llm_text[0] and len(llm_text[0]["texts"]) > 0:
            logger.info("Response sample text: {}".format(llm_text[0]['texts'][0]['text']))

        # 오류가 있는 경우에만 error 필드 추가
        if final_data.get("error") or graph_state.get("error"):
            result["error"] = final_data.get("error") or graph_state.get("error")

        graph_state["final_result"] = result
        logger.info("번역 결과 조합 노드 완료")
        return graph_state

    except Exception as e:
        logger.error(f"번역 결과 조합 노드 오류: {str(e)}", exc_info=True)
        graph_state["error"] = str(e)
        state_data = graph_state["state"]
        graph_state["final_result"] = {
            "state": "Incompleted",
            "llmText": [],
            "target": state_data.get("target"),
            "error": str(e)
        }
        return graph_state


# LangGraph 워크플로우 클래스
class TranslationWorkflowGraph(BaseWorkflowGraph):
    """Translation LangGraph 워크플로우"""

    def __init__(self):
        super().__init__("translation")

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        workflow = StateGraph(TranslationGraphState)

        # 노드 추가
        workflow.add_node("translate", translate_node)
        workflow.add_node("assemble_results", assemble_translation_results_node)

        # 엣지 정의
        workflow.set_entry_point("translate")
        workflow.add_edge("translate", "assemble_results")
        workflow.add_edge("assemble_results", END)

        return workflow


async def process_translation_workflow(state: dict, model: str) -> dict:
    """번역 워크플로우 실행 (LangGraph 기반)"""
    try:
        logger.info("LangGraph 기반 번역 워크플로우 시작")

        # LangGraph 워크플로우 생성
        workflow_graph = TranslationWorkflowGraph()

        # 초기 상태 준비
        initial_state: TranslationGraphState = {
            "state": state,
            "model": model,
            "translation_result": {},
            "final_result": {},
            "error": ""
        }

        # 워크플로우 실행
        final_state = await workflow_graph.execute(initial_state)

        # 결과 반환
        return final_state.get("final_result", {
            "state": "Incompleted",
            "llmText": [],
            "target": state.get("target"),
            "error": final_state.get("error", "알 수 없는 오류")
        })

    except Exception as e:
        logger.error(f"번역 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 응답 구성
        error_response = {
            "state": "Incompleted",
            "llmText": [],
            "target": state.get("target"),
            "error": str(e)
        }
        return error_response

async def process_translation_workflow_wrapper(request_data) -> dict:
    """API 요청을 처리하는 wrapper 함수 - 문장 분리 포함"""
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

        # llmText 가져오기
        llm_text = request_dict.get("llmText", [])

        logger.info(f"번역 요청 받음 - 페이지 수: {len(llm_text)}")

        # 상태 초기화 (원본 텍스트 그대로 사용 - 문장 분리 제거)
        # translate_with_index_mapping()에서 모든 텍스트를 한 번에 번역하므로
        # 사전 문장 분리는 불필요하고 오히려 성능 저하를 유발함
        state = {
            "llmText": llm_text,
            "target": request_dict.get("target")
        }

        logger.info(f"번역 워크플로우 실행 - 총 {len(llm_text)} 페이지 (원본 구조 유지)")

        # 워크플로우 실행 (model 전달)
        result = await process_translation_workflow(state, model=model)

        return result
    except Exception as e:
        logger.error(f"번역 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        error_response = {
            "state": "Incompleted",
            "llmText": [],
            "target": "ko",
            "error": str(e)
        }
        return error_response
