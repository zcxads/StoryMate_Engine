import os
import json
import aiohttp
import asyncio
import traceback
from pydantic import BaseModel
from typing import Any, Dict, Tuple, List

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate
from app.utils.language import language_generator

from app.utils.logger.setup import setup_logger
from app.utils.language.embedding import get_embedding
from app.utils.vectordb import get_similar_background_music
from app.models.state import get_valid_sound_state, BackgroundMusic
from app.prompts.language.sound.summation import get_text_summarization_prompt_config
from app.prompts.language.sound.book import get_book_background_music_selection_prompt_config
from app.utils.language.generator import language_generator

# 로거 설정
logger = setup_logger('book_bgm', 'logs/sound')

class BackgroundMusicSelection(BaseModel):
    selection: BackgroundMusic


async def select_best_background_music_with_llm(text: str, similar_music: List[Dict[str, Any]], **kwargs) -> Tuple[Dict[str, Any], str]:
    """언어 모델을 사용하여 주어진 배경음악 목록에서 가장 적절한 것을 선택합니다."""
    try:
        # 프롬프트 설정 가져오기
        prompt_config = get_book_background_music_selection_prompt_config()
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

        response = await language_generator.ainvoke(
            prompt.format(
                text=text,
                musics=musics_description
            ),
            config={"model": kwargs.get("model", "gemini")}
        )

        response_text = response.content

        # 응답 로깅 - 디버깅용
        logger.info(f"LLM 응답: {response_text}")
        
        # 선택된 번호 추출
        try:
            # 정규표현식을 사용하여 숫자만 추출
            import re
            selection_match = re.search(r'선택:\s*(\d+)', response_text)
            if selection_match:
                selected_index = int(selection_match.group(1)) - 1
            else:
                # 다른 패턴 시도
                selection_match = re.search(r'(\d+)\s*번', response_text)
                if selection_match:
                    selected_index = int(selection_match.group(1)) - 1
                else:
                    # 어떤 방식으로도 추출할 수 없으면 첫 번째 사용
                    logger.warning("선택 번호를 추출할 수 없어 첫 번째 음악 사용")
                    selected_index = 0
        except Exception as e:
            logger.error(f"선택 번호 추출 실패: {str(e)}")
            selected_index = 0
            
        # 선택 이유 추출
        try:
            reason_match = re.search(r'이유:\s*(.+)', response_text, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
            else:
                # 선택 이유를 찾지 못한 경우
                reason = "책의 전반적인 분위기와 주제에 적합한 배경음악"
        except Exception as e:
            logger.error(f"이유 추출 실패: {str(e)}")
            reason = "책의 분위기에 적합한 배경음악"
            
        # 유효한 인덱스 범위 확인
        if selected_index < 0 or selected_index >= len(similar_music):
            logger.warning(f"유효하지 않은 인덱스: {selected_index}, 첫 번째 음악 사용")
            selected_index = 0

        return similar_music[selected_index], reason

    except Exception as e:
        logger.error(f"LLM 선택 중 오류 발생: {str(e)}")
        return similar_music[0], f"오류로 인한 기본 선택: {str(e)}"


@traceable(run_type="chain")
async def book_background_music_agent(state: Dict[str, Any], **kwargs) -> Tuple[Dict[str, Any], str]:
    try:
        logger.info("책 전체 배경음악 생성 프로세스 시작")
        current_state = get_valid_sound_state(state)
        
        # 모든 페이지의 텍스트를 하나로 결합
        all_text = ""
        for page in current_state.pages:
            page_text = "\n".join([t.text for t in page.texts])
            all_text += page_text + "\n\n"
        
        # 임베딩 전에 텍스트를 요약하여 토큰 제한 내로 만들기
        logger.info("책 전체 텍스트 요약 시작")
        try:
            summarized_text = await summarize_text(all_text)
            logger.info("책 전체 텍스트 요약 완료")
            
            # 요약된 텍스트로 임베딩 가져오기
            embedding = await get_embedding(summarized_text)
            logger.info("요약된 텍스트의 임베딩 생성 완료")
        except Exception as e:
            # 요약에 실패하였으낙 더 짧게 잘라서 사용
            logger.error(f"텍스트 요약 및 임베딩 오류: {str(e)}")
            short_text = all_text[:1000]  # 매우 짧게 잔라서 사용
            embedding = await get_embedding(short_text)
            logger.info("짧게 잘라낸 텍스트의 임베딩 생성 완료")
        
        # 유사한 배경음악 검색
        similar_music = await get_similar_background_music(embedding)
        logger.info(f"책 전체에 대해 {len(similar_music)}개의 유사 배경음악 찾음")
        
        if similar_music:
            # 언어 모델을 사용하여 가장 적절한 배경음악 선택
            best_match, selection_reason = await select_best_background_music_with_llm(all_text, similar_music)
            
            # 선택된 배경음악을 모든 페이지에 동일하게 적용
            # 음악 경로 형식 생성 (상황_카테고리.mp3 형식)
            situation = best_match['payload'].get('situation', 'None')
            categories = best_match['payload'].get('categories', 'None')
            music_path = f"{situation}_{categories}.mp3"
            
            book_music = BackgroundMusic(
                pageKey=0,  # 책 전체를 나타내는 특별한 pageKey
                musicPath=music_path,
                situation=situation,
                categories=categories,
                similarityScore=f"{best_match['score']:.4f}",
                reason=selection_reason
            )
            
            # 각 페이지에 동일한 배경음악 할당
            current_state.background_music = [book_music]
            return {"state": current_state.model_dump()}, "completed"
        else:
            logger.warning("책에 대한 유사 배경음악을 찾지 못함")
            default_music = BackgroundMusic(
                pageKey=0,
                musicPath="None.mp3",
                situation="None",
                categories="None",
                similarityScore="0.0",
                reason="일치하는 배경음악을 찾지 못함"
            )
            
            current_state.background_music = [default_music]
            return {"state": current_state.model_dump()}, "completed"

    except Exception as e:
        logger.error(f"책 배경음악 에이전트 오류 발생: {str(e)}")
        logger.error(f"오류 추적: {traceback.format_exc()}")
        raise


async def summarize_text(text: str) -> str:
    """텍스트가 너무 길 경우 임베딩 토큰 제한(512 토큰) 이내로 요약합니다."""
    try:
        # 프롬프트 설정 가져오기
        prompt_config = get_text_summarization_prompt_config()
        template = prompt_config["template"]

        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"]
        )

        response = await language_generator.ainvoke(
            prompt.format(text=text),
            config={"model": "gemini"}  # 요약은 기본적으로 gemini 사용
        )
        return response.content
    except Exception as e:
        logger.error(f"텍스트 요약 중 오류 발생: {str(e)}")
        # 오류 발생 시 원본 텍스트의 앞부분 반환 (토큰 제한을 고려하여 매우 짧게 반환)
        return text[:1000]
