import asyncio
import logging
from typing import Dict, Any

from app.models.state import get_valid_sound_state, SoundState

from app.services.language.sound.sentence import sound_effect_agent
from app.services.language.sound.page import background_music_agent
from app.services.language.sound.position import sound_effect_position_agent

logger = logging.getLogger(__name__)


def create_page_specific_state(state: SoundState, page_key: int) -> Dict[str, Any]:
    """
    특정 페이지에 대한 상태만을 포함하는 새로운 상태를 생성합니다.
    """
    page = next((p for p in state.pages if p.pageKey == page_key), None)
    if not page:
        raise ValueError(f"Page {page_key} not found in state")

    # 해당 페이지만 포함하는 새로운 상태 생성
    page_state = SoundState(
        pages=[page],  # 현재 페이지만 포함
        background_music=[bm for bm in state.background_music if bm.pageKey == page_key] if state.background_music else None,
        sound_effects=[],
        effect_positions=[]
    )

    return page_state.model_dump()


async def orchestrate_agents(initial_state: Dict[str, Any], model: str = "gemini") -> Dict[str, Any]:
    """
    음악/효과음 에이전트들을 조율하여 실행합니다.
    """
    try:
        current_state = get_valid_sound_state(initial_state)

        # 1. 배경음악 선택 (전체 책 정보 기반 순차 실행)
        logger.info("Starting background music selection")
        state, _ = await background_music_agent(current_state.model_dump(), model=model)
        current_state = get_valid_sound_state(state)
        logger.info("Completed background music selection")

        # 2. 효과음 선택 (페이지별 병렬 실행)
        page_keys = [page.pageKey for page in current_state.pages]
        logger.info(f"Starting sound effect selection for pages: {page_keys}")

        # 각 페이지별로 효과음 선택을 병렬로 실행
        sound_effect_tasks = []
        for page_key in page_keys:
            # 각 페이지별 상태 생성
            page_state = create_page_specific_state(current_state, page_key)
            
            # sound_effect_agent는 이제 비동기 함수이므로 직접 호출
            task = sound_effect_agent(page_state, page_key, model)
            sound_effect_tasks.append(task)

        # 모든 효과음 선택 결과 수집
        sound_effect_results = await asyncio.gather(*sound_effect_tasks)
        
        # 결과 병합
        current_state.sound_effects = []
        for state_result, _ in sound_effect_results:
            result_state = get_valid_sound_state(state_result)
            if result_state.sound_effects:
                current_state.sound_effects.extend(result_state.sound_effects)

        logger.info("Completed sound effect selection")

        # 3. 효과음 포지션 선택 (페이지별 병렬 실행)
        logger.info("Starting sound effect position selection")

        position_tasks = []
        for page_key in page_keys:
            # 각 페이지별 상태 생성
            page_state = create_page_specific_state(current_state, page_key)

            # 해당 페이지의 효과음 정보 추가
            page_effects = next(
                (e for e in current_state.sound_effects if e.pageKey == page_key), None)
            if page_effects:
                page_state["sound_effects"] = [page_effects.model_dump()]

            # 비동기 태스크 생성 - sound_effect_position_agent는 이미 async 함수
            task = sound_effect_position_agent(page_state, page_key, model)
            position_tasks.append(task)

        # 모든 포지션 선택 결과 수집
        position_results = await asyncio.gather(*position_tasks)

        # 결과 병합
        current_state.effect_positions = []
        for state_result, _ in position_results:
            result_state = get_valid_sound_state(state_result)
            if result_state.effect_positions:
                current_state.effect_positions.extend(result_state.effect_positions)

        logger.info("Completed sound effect position selection")

        return current_state.model_dump()

    except Exception as e:
        logger.error(f"Error in orchestrate_agents: {str(e)}", exc_info=True)
        raise
