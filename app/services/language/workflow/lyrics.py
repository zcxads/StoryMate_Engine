import os
import json
from dotenv import load_dotenv

from app.models.language.lyrics import SongLyricsRequest
from app.models.language.lyrics import SongLyricsResponse
from app.models.state import LyricsState, Page, PageText, get_valid_lyrics_state, serialize_for_json

from app.services.language.lyrics.generator import lyrics_generator
from app.services.language.lyrics.formatter import lyrics_formatter
from app.utils.logger.setup import setup_logger

# 환경 변수 로드
load_dotenv()
logger = setup_logger('lyrics_workflow', 'logs/services')

async def process_lyrics_workflow(state: LyricsState, model: str = "gemini") -> dict:
    """노래 가사 생성 워크플로우 실행"""
    try:
        # LangGraph 대신 직접적인 비동기 호출
        # 1. Generator 단계
        generator_result = await lyrics_generator({"state": state.model_dump()}, model=model)
        
        # 2. Formatter 단계  
        final_result = await lyrics_formatter(generator_result, model=model)
        
        # 최종 상태 가져오기
        final_state = get_valid_lyrics_state(final_result)
        
        return {
            "state": "Completed" if final_state.formatted_lyrics else "Incompleted",
            "songTitle": final_state.raw_lyrics.get("songTitle") if final_state.raw_lyrics else None,
            "lyrics": final_state.formatted_lyrics if isinstance(final_state.formatted_lyrics, list) else []
        }
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
        model = request_dict.get("model", "gemini")
        
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
            language=request_dict.get('language', 'ko')
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
