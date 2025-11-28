import os
import json
from dotenv import load_dotenv

from app.models.language.sound import SoundRequest
from app.models.state import SoundState, SoundPage, PageText, get_valid_sound_state
from app.services.language.sound.orchestrate import orchestrate_agents
from app.utils.logger.setup import setup_logger

# 환경 변수 로드
load_dotenv()
logger = setup_logger('sound_workflow', 'logs/services')

async def process_sound_workflow(state: SoundState, model: str = "gemini") -> dict:
    """오디오 워크플로우 실행"""
    try:
        # model 파라미터를 전달하여 orchestrate_agents 실행
        final_state = await orchestrate_agents(state.model_dump(), model=model)
        final_state = get_valid_sound_state(final_state)
        sound_result = {
            "state": "Completed",
            "pages": [
                {
                    "pageKey": page.pageKey,
                    "backgroundMusic": next(
                        (music.to_dict() for music in final_state.background_music if music.pageKey == page.pageKey),
                        None
                    ),
                    "soundEffects": next(
                        (effects.to_dict() for effects in final_state.sound_effects if effects.pageKey == page.pageKey),
                        None
                    ),
                    "effectPositions": next(
                        (positions.to_dict() for positions in final_state.effect_positions if positions.pageKey == page.pageKey),
                        None
                    )
                }
                for page in state.pages
            ]
        }
        return sound_result
    except Exception as e:
        logger.error(f"오디오 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "error": str(e),
            "pages": []
        }

async def process_sound_workflow_wrapper(request_data) -> dict:
    """
    API 요청을 받아 SoundState 객체로 변환한 후,
    오디오 처리 워크플로우를 실행하고 결과를 반환하는 wrapper 함수.
    """
    try:
        # model 필드 추출
        model = request_data.get("model", "gemini") if isinstance(request_data, dict) else getattr(request_data, "model", "gemini")
            
        sound_pages = []
        llm_text = request_data["llmText"] if isinstance(request_data, dict) else request_data.llmText
        
        for page in llm_text:
            texts = [PageText(text=line["text"]) for line in page["texts"] if line.get("text")]
            sound_pages.append(SoundPage(pageKey=page["pageKey"], texts=texts))
            
        state = SoundState(pages=sound_pages)
        result = await process_sound_workflow(state, model=model)
        
        return result
    except Exception as e:
        logger.error(f"오디오 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "state": "Incompleted",
            "error": str(e),
            "pages": []
        }

# Kafka 서비스용 프로세서 함수
async def process_sound(request: SoundRequest):
    """Kafka Service가 호출할 프로세서 함수"""
    try:
        # 요청을 사전으로 변환
        request_dict = request.dict() if hasattr(request, 'dict') else request
        
        # 처리 실행
        logger.info("Processing sound request via Kafka Service")
        result = await process_sound_workflow_wrapper(request_dict)
        
        return result
    except Exception as e:
        logger.error(f"Kafka 서비스 오디오 처리 중 오류: {str(e)}", exc_info=True)
        # 오류 응답 구성
        error_response = {
            "state": "Incompleted",
            "error": str(e),
            "pages": []
        }
        return error_response
