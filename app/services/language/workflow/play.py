import os
import json
from app.utils.logger.setup import setup_logger
import time
from dotenv import load_dotenv

from app.models.language.play import PlayRequest
from app.models.state import Page, PageText, serialize_for_json, PlayState, get_valid_play_state
from app.services.language.play.generator import play_generator
from app.services.language.play.formatter import play_formatter

load_dotenv()
logger = setup_logger('workflow_play')


async def process_play_workflow(state, model) -> dict:
    """연극 대사 생성 워크플로우 실행"""
    # LangGraph 대신 직접적인 비동기 호출
        # 1. Generator 단계
    generator_result = await play_generator({"state": state.model_dump()}, model=model)
    
    # 2. Formatter 단계  
    final_result = await play_formatter(generator_result, model=model)
    
    # 최종 상태 가져오기
    final_state = get_valid_play_state(final_result)
    
    return {
        "state": "Completed" if final_state.formatted_play else "Incompleted",
        "message": "Completion of the creation of theatrical lines" if final_state.formatted_play else "Failure to generate theatrical lines",
        "playTitle": final_state.raw_play.get("playTitle") if final_state.raw_play else None,
        "script": final_state.formatted_play if isinstance(final_state.formatted_play, list) else []
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
        model = request_dict.get("model", "gemini")
        
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