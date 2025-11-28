import os
import json
import asyncio
import traceback
from pydantic import BaseModel
from typing import Any, Dict, Tuple, List
import re

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate

from app.utils.logger.setup import setup_logger
from app.utils.language.embedding import get_embedding
from app.utils.vectordb import get_similar_background_music
from app.utils.language.generator import language_generator

from app.models.state import get_valid_sound_state, BackgroundMusic
from app.prompts.language.sound.page import get_background_music_selection_prompt_config
from app.repositories.sound_generator import SoundGeneratorRepository
from app.core.config import settings
import logging
from datetime import datetime
import time

# 로거 설정
logger = setup_logger('page_bgm', 'logs/sound')

# Sound Generator Repository 초기화
sound_repo = SoundGeneratorRepository()

class BackgroundMusicSelections(BaseModel):
    selections: List[BackgroundMusic]


async def select_best_background_music_with_llm(text: str, similar_music: List[Dict[str, Any]], model: str = "gemini") -> Tuple[Dict[str, Any], str]:
    """언어 모델을 사용하여 주어진 배경음악 목록에서 가장 적절한 것을 선택합니다."""
    try:
        # 프롬프트 설정 가져오기
        prompt_config = get_background_music_selection_prompt_config()
        template = prompt_config["template"]

        musics_description = "\n".join([
            f"{i+1}. 장면: {music['payload']['sentence']}\n"
            f"   상황: {music['payload'].get('situation', 'None')}\n"
            f"   카테고리: {music['payload'].get('categories', 'None')}\n"
            f"   유사도: {music['score']:.4f}\n"
            for i, music in enumerate(similar_music)
        ])

        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"]
        )

        try:
            response = await language_generator.ainvoke(
                prompt.format(
                    text=text,
                    musics=musics_description
                ),
                config={"model": model}
            )
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                logger.warning(f"Event loop error for text '{text}', using default selection")
                return similar_music[0], "Default selection due to event loop error"
            else:
                raise

        response_text = response.content
        # logger.info(f"LLM이 제시한 '{text}'에 대한 응답: {response_text}")

        selection_line = [line for line in response_text.split(
            '\n') if line.startswith('선택:')][0]
        selected_index = int(selection_line.split(':')[1].strip()) - 1

        reason_line = [line for line in response_text.split(
            '\n') if line.startswith('이유:')][0]
        reason = reason_line.split(':')[1].strip()

        return similar_music[selected_index], reason
        
    except Exception as e:
        logger.error(f"LLM 선택 중 오류 발생: {str(e)}")
        return similar_music[0], f"오류로 인한 기본 선택: {str(e)}"

async def generate_bgm_audio_file(bgm_text: str, filename: str) -> Tuple[bool, str, float]:
    """배경음악 텍스트를 실제 오디오 파일로 변환"""
    try:
        # Sound Generator를 사용하여 배경음악 생성
        success, ncp_url, audio_duration = await sound_repo.generate_background_music(
            description=bgm_text,
            filename=filename,
            text_content=bgm_text
        )
        
        if success:
            return True, ncp_url or "", audio_duration
        else:
            return False, "", 0.0
            
    except Exception as e:
        logger.error(f"배경음악 오디오 생성 실패: {str(e)}")
        return False, "", 0.0

async def process_single_page(page, model: str = "gemini"):
    """단일 페이지에 대한 배경음악 처리를 수행하는 비동기 함수"""
    try:
        # 페이지의 모든 텍스트를 하나로 결합
        page_text = "\n".join([t.text for t in page.texts])

        # 임베딩 가져오기
        embedding = await get_embedding(page_text)
        logger.info(f"페이지 {page.pageKey}의 임베딩 생성 완료")

        # 유사한 배경음악 검색
        similar_music = await get_similar_background_music(embedding)
        logger.info(f"페이지 {page.pageKey}에 대해 {len(similar_music)}개의 유사 배경음악 찾음")

        if similar_music:
            # 언어 모델을 사용하여 가장 적절한 배경음악 선택
            best_match, selection_reason = await select_best_background_music_with_llm(page_text, similar_music, model)
            
            # 배경음악 텍스트 추출
            bgm_text = best_match['payload']['sentence']
            
            # 파일명 생성 (sound_output 폴더용)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 텍스트에서 안전한 파일명 생성
            bgm_filename = f"background_music_{timestamp}.mp3"
            
            # sound_output 폴더 경로 사용
            sound_output_dir = settings.sound_output_dir
            os.makedirs(sound_output_dir, exist_ok=True)
            bgm_filepath = os.path.join(sound_output_dir, bgm_filename)
            
            logger.info(f"🎵 배경음악 파일 경로: {bgm_filepath}")
            
            # 실제 오디오 파일 생성 (타임아웃 조정)
            try:
                audio_success, ncp_url, audio_duration = await asyncio.wait_for(
                    generate_bgm_audio_file(bgm_text, bgm_filepath),
                    timeout=180.0
                )
                
                if audio_success and ncp_url:
                    return BackgroundMusic(
                        pageKey=page.pageKey,
                        musicPath=bgm_filename,
                        situation=best_match['payload'].get('situation', 'None'),
                        categories=best_match['payload'].get('categories', 'None'),
                        similarityScore=f"{best_match['score']:.4f}",
                        reason=selection_reason,
                        ncp_url=ncp_url,
                        duration=audio_duration
                    )
                else:
                    # 오디오 생성 실패 시 파일명만 반환
                    return BackgroundMusic(
                        pageKey=page.pageKey,
                        musicPath=bgm_filename,
                        situation=best_match['payload'].get('situation', 'None'),
                        categories=best_match['payload'].get('categories', 'None'),
                        similarityScore=f"{best_match['score']:.4f}",
                        reason=selection_reason,
                        ncp_url="",
                        duration=0.0
                    )
            except asyncio.TimeoutError:
                logger.warning(f"배경음악 생성 타임아웃: {bgm_text}")
                return BackgroundMusic(
                    pageKey=page.pageKey,
                    musicPath=bgm_filename,
                    situation=best_match['payload'].get('situation', 'None'),
                    categories=best_match['payload'].get('categories', 'None'),
                    similarityScore=f"{best_match['score']:.4f}",
                    reason=selection_reason,
                    ncp_url="",
                    duration=0.0
                )
        else:
            logger.warning(f"페이지 {page.pageKey}에 대한 유사 배경음악을 찾지 못함")
            return BackgroundMusic(
                pageKey=page.pageKey,
                musicPath="None.mp3",
                situation="None",
                categories="None",
                similarityScore="0.0",
                reason="일치하는 배경음악을 찾지 못함"
            )
    except Exception as e:
        logger.error(f"페이지 {page.pageKey} 처리 중 오류 발생: {str(e)}")
        logger.error(f"오류 추적: {traceback.format_exc()}")
        return BackgroundMusic(
            pageKey=page.pageKey,
            musicPath="None.mp3",
            situation="None",
            categories="None",
            similarityScore="0.0",
            reason=f"처리 중 오류 발생: {str(e)}"
        )

@traceable(run_type="chain")
async def background_music_agent(state: Dict[str, Any], **kwargs) -> Tuple[Dict[str, Any], str]:
    start_time = time.time()
    try:
        logger.info("배경음악 생성 프로세스 시작")
        current_state = get_valid_sound_state(state)
        
        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", "gemini")
        
        # 모든 페이지를 동시에 비동기적으로 처리
        pages = current_state.pages
        bgm_tasks = [process_single_page(page, model_name) for page in pages]
        bgm_results = await asyncio.gather(*bgm_tasks)
        
        # 결과를 상태에 추가
        if not current_state.background_music:
            current_state.background_music = []
        
        current_state.background_music.extend(bgm_results)
        
        execution_time = time.time() - start_time
        logger.info(f"배경음악 생성 프로세스 완료 (총 처리 시간: {execution_time:.2f}초)")
        
        return {"state": current_state.model_dump()}, "sound_effect"
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"배경음악 생성 프로세스 오류: {str(e)} (처리 시간: {execution_time:.2f}초)")
        raise
