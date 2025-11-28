import json
import asyncio
from dotenv import load_dotenv

from app.services.language.translation.translator import translation_agent
from app.utils.logger.setup import setup_logger
from app.models.language.translation import TranslationRequest

# 환경 변수 로드
load_dotenv()

# 로거 설정
logger = setup_logger('translation_workflow', 'logs/translation')

async def process_translation_workflow(state: dict, model: str = "gemini") -> dict:
    """번역 워크플로우 실행"""
    try:
        # 원본 상태 로깅
        logger.info("Original state llmText length: {}".format(len(state.get('llmText', []))))
        if state.get('llmText', []) and len(state.get('llmText', [])) > 0:
            sample_original = state['llmText'][0]
            if "texts" in sample_original and len(sample_original["texts"]) > 0:
                logger.info("Original sample text: {}".format(sample_original['texts'][0]))
        
        # LangGraph 대신 직접적인 비동기 호출
        final_result = await translation_agent({"state": state}, model=model)
        
        # 최종 상태 가져오기 및 확인
        final_data = final_result.get("state", {})
        logger.info("Final state keys: {}".format(final_data.keys() if isinstance(final_data, dict) else 'Not a dict'))
        
        # 중요: 번역된 llmText 확인 및 로깅
        llm_text = final_data.get("llmText", [])
        logger.info("Final llmText length: {}".format(len(llm_text)))
        if llm_text and len(llm_text) > 0:
            sample_page = llm_text[0]
            if "texts" in sample_page and len(sample_page["texts"]) > 0:
                logger.info("Sample translated text: {}".format(sample_page['texts'][0]['text']))
                
        # 사용할 최종 상태
        final_state = final_data
        
        # 기본 응답 구성 - 번역 표시자 추가
        result = {
            "state": "Completed" if not final_state.get("error") else "Incompleted",
            "llmText": llm_text,
            "target": final_state.get("target", "ko"),
            "translated": True  # 번역 완료 표시
        }
        
        # 추가 로깅
        logger.info("Returning response with {} llmText items".format(len(llm_text)))
        if llm_text and len(llm_text) > 0 and "texts" in llm_text[0] and len(llm_text[0]["texts"]) > 0:
            logger.info("Response sample text: {}".format(llm_text[0]['texts'][0]['text']))
        
        # 오류가 있는 경우에만 error 필드 추가
        if final_state.get("error"):
            result["error"] = final_state.get("error")
        
        return result
    except Exception as e:
        logger.error(f"번역 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 응답 구성
        error_response = {
            "state": "Incompleted",
            "llmText": [],
            "target": state.get("target", "ko"),
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
        model = request_dict.get("model", "gemini")

        # llmText 가져오기
        llm_text = request_dict.get("llmText", [])

        logger.info(f"번역 요청 받음 - 페이지 수: {len(llm_text)}")

        # 상태 초기화 (원본 텍스트 그대로 사용 - 문장 분리 제거)
        # translate_with_index_mapping()에서 모든 텍스트를 한 번에 번역하므로
        # 사전 문장 분리는 불필요하고 오히려 성능 저하를 유발함
        state = {
            "llmText": llm_text,
            "target": request_dict.get("target", "ko")
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
