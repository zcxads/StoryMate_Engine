import os
import logging
import asyncio
import traceback
from pydantic import BaseModel
from typing import Any, Dict, Tuple, List

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate

from app.utils.vectordb import get_similar_effects

from app.utils.language.embedding import get_embedding
from app.utils.language.generator import language_generator
from app.models.state import get_valid_sound_state, PageSoundEffects, SoundEffect
from app.prompts.language.sound.sentence import get_sound_effect_selection_prompt_config
from app.repositories.sound_generator import SoundGeneratorRepository
from app.core.config import settings
import re
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Sound Generator Repository 초기화
sound_repo = SoundGeneratorRepository()


class SoundEffectSelections(BaseModel):
    effects: List[SoundEffect]


async def select_best_effect_with_llm(text: str, similar_effects: List[Dict[str, Any]], model: str = "gemini") -> Tuple[Dict[str, Any], str]:
    """언어 모델을 사용하여 주어진 효과음 목록에서 가장 적절한 것을 선택합니다."""
    try:
        # 프롬프트 설정 가져오기
        prompt_config = get_sound_effect_selection_prompt_config()
        template = prompt_config["template"]

        effects_description = "\n".join([
            f"{i+1}. 장면: {effect['payload']['sentence']}\n"
            f"   상황: {effect['payload'].get('situation', 'None')}\n"
            f"   환경: {effect['payload'].get('environment', 'None')}\n"
            f"   동작: {effect['payload'].get('action', 'None')}\n"
            f"   감정: {effect['payload'].get('affect', 'None')}\n"
            f"   유사도: {effect['score']:.4f}\n"
            for i, effect in enumerate(similar_effects)
        ])

        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"]
        )
        
        try:
            response = await language_generator.ainvoke(
                prompt.format(
                    text=text,
                    effects=effects_description
                ),
                config={"model": model}
            )
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                logger.warning(f"Event loop error for text '{text}', using default selection")
                return similar_effects[0], "Default selection due to event loop error"
            else:
                raise

        # 응답 파싱
        response_text = response.content
        logger.info(f"LLM Response for '{text}': {response_text}")

        # 선택된 번호 추출 (1-based index) - 오류 처리 강화
        try:
            selection_lines = [line for line in response_text.split('\n') if line.startswith('선택:')]
            if not selection_lines:
                logger.warning(f"No selection line found in response: {response_text}")
                return similar_effects[0], "Default selection - no selection found in response"
                
            selection_line = selection_lines[0]
            selection_text = selection_line.split(':')[1].strip()
            
            # 괄호나 다른 문자가 포함된 경우 처리
            import re
            numbers = re.findall(r'\d+', selection_text)
            if not numbers:
                logger.warning(f"No number found in selection: {selection_text}")
                return similar_effects[0], "Default selection - no valid number in selection"
                
            selected_index = int(numbers[0]) - 1
            
            # 인덱스 범위 체크
            if selected_index < 0 or selected_index >= len(similar_effects):
                logger.warning(f"Invalid selection index {selected_index}, using first effect")
                selected_index = 0

        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing selection: {e}. Using first effect.")
            selected_index = 0

        # 선택 이유 추출
        try:
            reason_lines = [line for line in response_text.split('\n') if line.startswith('이유:')]
            if reason_lines:
                reason = reason_lines[0].split(':', 1)[1].strip()
            else:
                reason = "No reason provided"
        except (IndexError, ValueError):
            reason = "Error extracting reason"

        return similar_effects[selected_index], reason
        
    except Exception as e:
        logger.error(f"Error in LLM selection: {str(e)}")
        return similar_effects[0], f"Default selection due to error: {str(e)}"

async def generate_effect_audio_file(effect_text: str, filename: str, additional_info: dict = None) -> Tuple[bool, str]:
    """효과음 텍스트를 실제 오디오 파일로 변환"""
    start_time = time.time()
    try:
        logger.info(f"🔊 효과음 오디오 생성 시작: {effect_text}")
        logger.info(f"🔊 파일명: {filename}")
        if additional_info:
            logger.info(f"🔊 추가 정보: {additional_info}")
        
        # Sound Generator를 사용하여 효과음 생성 (추가 정보 포함)
        success, ncp_url, audio_duration = await sound_repo.generate_sound_effect(
            description=effect_text,  # 벡터 DB의 sentence
            filename=filename,
            additional_info=additional_info
        )
        
        execution_time = time.time() - start_time
        logger.info(f"🔊 효과음 생성 결과: success={success}, ncp_url={ncp_url}")
        logger.info(f"🔊 총 처리 시간: {execution_time:.2f}초")
        
        if success:
            return True, ncp_url or ""
        else:
            logger.error(f"❌ 효과음 오디오 생성 실패: {effect_text}")
            return False, ""
            
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 효과음 오디오 생성 중 예외 발생: {effect_text} - {str(e)}")
        logger.error(f"❌ 처리 시간: {execution_time:.2f}초")
        logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
        return False, ""

async def process_single_text(text, model: str = "gemini"):
    """단일 텍스트에 대한 효과음 처리를 수행하는 비동기 함수"""
    try:
        # 임베딩 가져오기
        embedding = await get_embedding(text.text)
        logger.info(f"Got embedding for text '{text.text}': {len(embedding)} dimensions")

        # 유사한 효과음 검색
        similar_effects = await get_similar_effects(embedding)
        logger.info(f"Found {len(similar_effects)} similar effects for '{text.text}'")

        if similar_effects:
            # 언어 모델을 사용하여 가장 적절한 효과음 선택
            best_match, selection_reason = await select_best_effect_with_llm(text.text, similar_effects, model)
            
            # 효과음 텍스트 추출
            effect_text = best_match['payload']['sentence']
            
            # 파일명 생성 (sound_output 폴더용)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 텍스트에서 안전한 파일명 생성
            effect_filename = f"sound_effect_{timestamp}.mp3"
            
            # sound_output 폴더 경로 사용
            sound_output_dir = settings.sound_output_dir
            os.makedirs(sound_output_dir, exist_ok=True)
            effect_filepath = os.path.join(sound_output_dir, effect_filename)
            
            logger.info(f"🔊 효과음 파일 경로: {effect_filepath}")
            
            # 추가 정보 구성
            additional_info = {
                'situation': best_match['payload'].get('situation', ''),
                'environment': best_match['payload'].get('environment', ''),
                'action': best_match['payload'].get('action', ''),
                'affect': best_match['payload'].get('affect', '')
            }
            
            # 실제 오디오 파일 생성 (타임아웃 조정)
            try:
                audio_success, ncp_url = await asyncio.wait_for(
                    generate_effect_audio_file(effect_text, effect_filepath, additional_info),
                    timeout=180.0
                )
                
                if audio_success and ncp_url:
                    # 효과음 생성 성공
                    return SoundEffect(
                        text=text.text,
                        effectPath=effect_filename,
                        situationInfo=best_match['payload'].get('situation', 'None'),
                        environmentInfo=best_match['payload'].get('environment', 'None'),
                        actionInfo=best_match['payload'].get('action', 'None'),
                        affectInfo=best_match['payload'].get('affect', 'None'),
                        similarityScore=f"{best_match['score']:.4f}",
                        reason=selection_reason,
                        ncp_url=ncp_url
                    )
                else:
                    # 효과음 생성 실패 시 기본 효과음 사용
                    logger.warning(f"❌ 효과음 생성 실패: {effect_text}")
                    logger.warning(f"   - audio_success: {audio_success}")
                    logger.warning(f"   - ncp_url: {ncp_url}")
                    return SoundEffect(
                        text=text.text,
                        effectPath="None.mp3",  # 기본 효과음 파일명
                        situationInfo=best_match['payload'].get('situation', 'None'),
                        environmentInfo=best_match['payload'].get('environment', 'None'),
                        actionInfo=best_match['payload'].get('action', 'None'),
                        affectInfo=best_match['payload'].get('affect', 'None'),
                        similarityScore=f"{best_match['score']:.4f}",
                        reason=f"{selection_reason} (기본 효과음 사용)",
                        ncp_url=""
                    )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ 효과음 생성 타임아웃: {effect_text}")
                return SoundEffect(
                    text=text.text,
                    effectPath=effect_filename,
                    situationInfo=best_match['payload'].get('situation', 'None'),
                    environmentInfo=best_match['payload'].get('environment', 'None'),
                    actionInfo=best_match['payload'].get('action', 'None'),
                    affectInfo=best_match['payload'].get('affect', 'None'),
                    similarityScore=f"{best_match['score']:.4f}",
                    reason=f"{selection_reason} (타임아웃)",
                    ncp_url=""
                )
            except Exception as e:
                logger.error(f"❌ 효과음 생성 중 예외 발생: {effect_text} - {str(e)}")
                return SoundEffect(
                    text=text.text,
                    effectPath="None.mp3",
                    situationInfo=best_match['payload'].get('situation', 'None'),
                    environmentInfo=best_match['payload'].get('environment', 'None'),
                    actionInfo=best_match['payload'].get('action', 'None'),
                    affectInfo=best_match['payload'].get('affect', 'None'),
                    similarityScore=f"{best_match['score']:.4f}",
                    reason=f"{selection_reason} (예외: {str(e)})",
                    ncp_url=""
                )
        else:
            logger.warning(f"No similar effects found for text: {text.text}")
            return SoundEffect(
                text=text.text,
                effectPath="None.mp3",
                situationInfo="None",
                environmentInfo="None",
                actionInfo="None",
                affectInfo="None",
                similarityScore="0.0",
                reason="No matching effects found"
            )
    except Exception as e:
        logger.error(f"Error processing text: {text.text}. Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return SoundEffect(
            text=text.text,
            effectPath="None.mp3",
            situationInfo="None",
            environmentInfo="None",
            actionInfo="None",
            affectInfo="None",
            similarityScore="0.0",
            reason=f"Error during processing: {str(e)}"
        )


@traceable(run_type="chain")
async def sound_effect_agent(state: Dict[str, Any], pageKey: int, model: str = "gemini") -> Tuple[Dict[str, Any], str]:
    """효과음 선택 에이전트 - 비동기 함수로 변경"""
    start_time = time.time()
    try:
        current_state = get_valid_sound_state(state)

        page = next(
            (page for page in current_state.pages if page.pageKey == pageKey),
            None
        )

        if page is None:
            raise ValueError(f"No content found for pageKey: {pageKey}")

        # 모든 텍스트를 동시에 비동기적으로 처리
        effects = await asyncio.gather(*[
            process_single_text(text, model) for text in page.texts
        ])

        if not current_state.sound_effects:
            current_state.sound_effects = []

        current_state.sound_effects.append(PageSoundEffects(
            pageKey=pageKey,
            effects=effects
        ))

        execution_time = time.time() - start_time
        logger.info(f"효과음 생성 프로세스 완료 (페이지 {pageKey}, 총 처리 시간: {execution_time:.2f}초)")

        return {"state": current_state.model_dump()}, "sound_effect_position"

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error in sound_effect_agent: {str(e)} (처리 시간: {execution_time:.2f}초)")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
