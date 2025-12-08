import re
from typing import Any, Dict, Tuple

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate

from app.models.state import get_valid_state
from app.utils.logger.setup import setup_logger
from app.prompts.language.orthography import get_proofreading_prompt_config
from app.utils.language.generator import language_generator
from app.services.language.orthography.contextual import filter_ai_generated_comments
from app.config import settings

# 로거 설정
logger = setup_logger('orthography_proofreading', 'logs/orthography')

@traceable(run_type="chain")
async def proofreading_agent_per_page(page_text: str, page_key: int, language: str, **kwargs) -> str:
    """개별 페이지에 대한 맞춤법 교정 처리

    Args:
        page_text: 교정할 텍스트
        page_key: 페이지 키
        language: 언어 코드 (ko, en, ja, zh 등)
        **kwargs: 추가 파라미터 (model 등)
    """
    try:
        logger.info(f"페이지 {page_key} 교정 프로세스 시작 (언어: {language})")

        # 빈 텍스트 처리
        if not page_text or page_text.strip() == '':
            logger.info(f"페이지 {page_key} 텍스트가 비어있음")
            return ''

        # 언어별 프롬프트 설정 가져오기
        prompt_config = get_proofreading_prompt_config(language=language)

        prompt = PromptTemplate(
            template=prompt_config["template"],
            input_variables=prompt_config["input_variables"]
        )

        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", settings.default_llm_model)

        logger.info(f"페이지 {page_key} 교정 체인 실행 (언어: {language}, 모델: {model_name})")
        chain = prompt | language_generator

        # LLM 결과를 텍스트로 받음
        result = await chain.ainvoke({"text": page_text}, config={"model": model_name})
        corrected_text = result.content.strip()

        # AI 생성 메타 코멘트 필터링
        corrected_text = filter_ai_generated_comments(corrected_text)

        logger.info(f"페이지 {page_key} 교정 완료, 원본 길이: {len(page_text)}, 교정 후 길이: {len(corrected_text)}")
        logger.debug(f"페이지 {page_key} 교정 결과: {corrected_text[:200]}...")

        return corrected_text

    except Exception as e:
        logger.error(f"페이지 {page_key} 교정 에이전트 오류 발생: {str(e)}", exc_info=True)
        # 오류 발생 시 원본 텍스트 반환
        return page_text

# 기존 함수 유지 (호환성을 위해)
@traceable(run_type="chain")
async def proofreading_agent(state: Dict[str, Any], **kwargs) -> Tuple[Dict[str, Any], str]:
    """기존 방식의 교정 에이전트 (전체 페이지 일괄 처리)"""
    try:
        logger.info("교정 프로세스 시작 (전체 페이지 일괄 처리)")
        # 상태 처리: 필요한 경우 OCRState로 변환
        current_state = get_valid_state(state)
        
        # 페이지 키 목록 준비 (로깅용)
        all_page_keys = [page.pageKey for page in current_state.pages]
        logger.info(f"전체 페이지 키: {all_page_keys}")
        logger.info(f"총 처리할 페이지 수: {len(all_page_keys)}")
        
        # 문맥을 위해 모든 텍스트를 하나의 문자열로 결합
        full_text = "\n\n".join([
            f"[Page {page.pageKey}]\n{' '.join([t.text for t in page.texts])}" 
            for page in current_state.pages
        ])
        
        # 프롬프트 설정 가져오기
        prompt_config = get_proofreading_prompt_config()
        template = prompt_config["template"]
        
        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"]
        )

        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", settings.default_llm_model)

        logger.info("교정 체인 실행")
        chain = prompt | language_generator
        
        # LLM 결과를 텍스트로 받음
        result = await chain.ainvoke({"text": full_text}, config={"model": model_name})
        corrected_text = result.content
        
        logger.info("LLM 결과 받음, 페이지별 처리 시작")
        logger.debug(f"LLM 결과: {corrected_text[:500]}...")
        
        # 텍스트 결과를 페이지별로 분리
        pages = []
        # 정규식으로 페이지 매칭
        page_pattern = re.compile(r'\[Page (\d+)\]\s*(.*?)(?=\[Page \d+\]|\Z)', re.DOTALL)
        matches = page_pattern.findall(corrected_text)
        
        processed_page_keys = set()
        
        # 매칭된 페이지 처리
        for page_key_str, page_text in matches:
            try:
                page_key = int(page_key_str)
                processed_page_keys.add(page_key)
                pages.append({
                    'pageKey': page_key,
                    'text': page_text.strip()
                })
                logger.debug(f"페이지 {page_key} 처리됨, 텍스트 길이: {len(page_text.strip())}")
            except ValueError:
                logger.error(f"페이지 키 변환 오류: {page_key_str}")
        
        # 누락된 페이지가 있는지 확인
        missing_page_keys = set(all_page_keys) - processed_page_keys
        if missing_page_keys:
            logger.warning(f"LLM 결과에서 누락된 페이지 키가 있습니다: {missing_page_keys}")
            for page_key in missing_page_keys:
                # 원본 페이지 찾기
                original_page = next((p for p in current_state.pages if p.pageKey == page_key), None)
                if original_page:
                    # 원본 텍스트를 사용
                    original_text = ' '.join([t.text for t in original_page.texts])
                    pages.append({
                        'pageKey': page_key,
                        'text': original_text
                    })
                    logger.info(f"페이지 {page_key}를 원본 텍스트로 추가했습니다: {original_text[:50]}...")
                else:
                    # 비어있는 페이지인 경우 비어있는 배열 추가
                    pages.append({
                    'pageKey': page_key,
                    'text': ''
                    })
                    logger.info(f"페이지 {page_key}를 빈 텍스트로 추가했습니다.")
        
        # 페이지 키 기준으로 정렬
        pages.sort(key=lambda x: x['pageKey'])
        
        current_state.candidate_proofread = pages
        logger.info(f"{len(pages)}개의 페이지 처리 완료, 전체 페이지 수: {len(all_page_keys)}")
        
        return {"state": current_state.model_dump()}, "contextual"
        
    except Exception as e:
        logger.error(f"교정 에이전트 오류 발생: {str(e)}", exc_info=True)
        logger.error(f"입력 상태: {state}")
        raise
