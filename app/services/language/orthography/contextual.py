import os
import re
from typing import List, Any, Dict, Tuple

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.models.state import get_valid_state, CorrectedPages
from app.utils.logger.setup import setup_logger
from app.prompts.language.orthography import get_contextual_prompt_config
from app.utils.language.generator import language_generator
from app.core.config import settings

# 로거 설정
logger = setup_logger('orthography_contextual', 'logs/orthography')

def filter_ai_generated_comments(text: str) -> str:
    """AI가 생성한 메타 코멘트를 필터링합니다."""
    if not text or not text.strip():
        return text
    
    # AI가 생성할 법한 메타 코멘트 패턴들
    ai_comment_patterns = [
        r'^(Okay,?\s*)?I\s+(have\s+)?reviewed?\s+the\s+text.*?\.?\s*',  # "Okay, I have reviewed the text"
        r'^Here\'?s\s+the\s+(improved|corrected|refined)\s+version:?\s*',  # "Here's the improved version:"
        r'^I\s+(understand|see|notice).*?\.?\s*',  # "I understand", "I see"
        r'^The\s+(corrected|improved|refined)\s+text\s+is:?\s*',  # "The corrected text is:"
        r'^\s*Below\s+is\s+the\s+(corrected|improved|refined)\s+text:?\s*',  # "Below is the corrected text:"
        r'^\s*I\'?m\s+(ready|here)\s+to\s+(help|correct).*?\.?\s*',  # "I'm ready to help"
        r'^\s*Please\s+find\s+the\s+(corrected|improved)\s+text.*?\.?\s*',  # "Please find the corrected text"
        r'^\s*After\s+(reviewing|analyzing).*?here\s+(is|are).*?\.?\s*',  # "After reviewing, here is..."
        r'^\s*I\s+have\s+applied\s+the\s+requested\s+refinements.*?\.?\s*',  # "I have applied the requested refinements"
        r'^\s*I\s+(will|shall)\s+(now\s+)?correct.*?\.?\s*',  # "I will now correct"
        r'^\s*Let\s+me\s+(correct|fix|improve).*?\.?\s*',  # "Let me correct"
        r'^\s*I\'?ve\s+(corrected|fixed|improved).*?\.?\s*',  # "I've corrected"
        r'^\s*I\s+have\s+refined\s+the\s+text.*?\.?\s*',  # "I have refined the text"
    ]
    
    cleaned_text = text.strip()
    
    # 각 패턴에 대해 필터링 수행 (대소문자 무시)
    for pattern in ai_comment_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # 남은 텍스트가 있는지 확인
    cleaned_text = cleaned_text.strip()
    
    # 줄바꿈으로 시작하는 경우 정리
    cleaned_text = re.sub(r'^\n+', '', cleaned_text)
    
    return cleaned_text

@traceable(run_type="chain")
async def contextual_agent_per_page(proofread_text: str, original_text: str, page_key: int, language: str, **kwargs) -> str:
    """개별 페이지에 대한 문맥 처리

    Args:
        proofread_text: 교정된 텍스트
        original_text: 원본 텍스트
        page_key: 페이지 키
        language: 언어 코드 (ko, en, ja, zh 등)
        **kwargs: 추가 파라미터 (model 등)
    """
    try:
        logger.info(f"페이지 {page_key} 문맥 처리 시작 (언어: {language})")

        # 빈 텍스트 처리
        if not proofread_text or proofread_text.strip() == '':
            logger.info(f"페이지 {page_key} 교정 텍스트가 비어있음")
            return original_text if original_text else ''

        # 단어 하나 또는 너무 짧을 경우 문맥 처리 스킵
        if len(proofread_text.split()) <= 2 and len(proofread_text) < 10:
            logger.info(f"페이지 {page_key}: 텍스트가 너무 짧아 문맥 처리 생략")
            logger.debug(f"페이지 {page_key} 문맥 처리 결과: {proofread_text[:200]}...")
            return proofread_text

        # 언어별 프롬프트 설정 가져오기
        prompt_config = get_contextual_prompt_config(language=language)

        prompt = PromptTemplate(
            template=prompt_config["template"],
            input_variables=prompt_config["input_variables"]
        )

        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", settings.default_llm_model)

        logger.info(f"페이지 {page_key} 문맥 체인 실행 (언어: {language}, 모델: {model_name})")
        chain = prompt | language_generator

        # LLM 호출 및 결과 받기
        result = await chain.ainvoke({
            "text": proofread_text,
            "original_text": original_text
        }, config={"model": model_name})

        # 결과 텍스트 처리
        corrected_text = result.content.strip()

        # AI 생성 메타 코멘트 필터링
        corrected_text = filter_ai_generated_comments(corrected_text)

        # 안전장치: 출력 길이 검증 (원본보다 짧거나 긴 경우)
        min_expected_length = len(proofread_text) * 0.5  # 원본의 50% 미만

        # 너무 짧은 경우
        if len(corrected_text) < min_expected_length:
            logger.warning(
                f"⚠️ 페이지 {page_key} Contextual 처리 결과가 비정상적으로 짧음! "
                f"원본(proofread): {len(proofread_text)}자 → 처리 후: {len(corrected_text)}자"
            )
            logger.warning(f"LLM 출력 내용: {corrected_text[:500]}")
            logger.warning(f"원본 교정 텍스트로 복원합니다.")
            return proofread_text

        # 원본보다 긴 경우
        if len(corrected_text) > len(proofread_text):
            logger.warning(
                f"⚠️ 페이지 {page_key} Contextual 처리 결과가 원본보다 김! "
                f"원본(proofread): {len(proofread_text)}자 → 처리 후: {len(corrected_text)}자"
            )
            logger.warning(f"LLM 출력 내용: {corrected_text[:500]}")
            logger.warning(f"원본 교정 텍스트로 복원합니다.")
            return proofread_text

        logger.info(f"페이지 {page_key} 문맥 처리 완료, 원본 길이: {len(proofread_text)}, 처리 후 길이: {len(corrected_text)}")
        logger.debug(f"페이지 {page_key} 문맥 처리 결과: {corrected_text[:200]}...")

        return corrected_text

    except Exception as e:
        logger.error(f"페이지 {page_key} 문맥 처리 에이전트 오류 발생: {str(e)}", exc_info=True)
        # 오류 발생 시 교정된 텍스트 반환, 없으면 원본 텍스트 반환
        return proofread_text if proofread_text else original_text

# 기존 함수 유지 (호환성을 위해)
@traceable(run_type="chain")
async def contextual_agent(state: Dict[str, Any], **kwargs) -> Tuple[Dict[str, Any], str]:
    """기존 방식의 문맥 처리 에이전트 (전체 페이지 일괄 처리)"""
    try:
        logger.info("문맥 텍스트 처리 시작 (전체 페이지 일괄 처리)")
        # 상태 처리
        current_state = get_valid_state(state)
        
        # 페이지 키 목록 준비 (로깅용)
        all_page_keys = [page.pageKey for page in current_state.pages]
        logger.info(f"전체 페이지 키: {all_page_keys}")
        logger.info(f"총 처리할 페이지 수: {len(all_page_keys)}")
        
        # 이전 에이전트의 결과에서 텍스트 구성
        proofread_text = "\n\n".join([
            f"[Page {page['pageKey']}]\n{page['text']}" 
            for page in current_state.candidate_proofread
        ])
        
        # 원본 텍스트도 참고용으로 포함
        original_text = "\n\n".join([
            f"[Page {page.pageKey}]\n{' '.join([t.text for t in page.texts])}" 
            for page in current_state.pages
        ])
        
        # 프롬프트 설정 가져오기
        prompt_config = get_contextual_prompt_config()
        template = prompt_config["template"]
        
        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"]
        )
        
        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", settings.default_llm_model)
        
        logger.info("문맥 체인 실행 시도")
        chain = prompt | language_generator
        
        # LLM 호출 및 결과 받기
        result = await chain.ainvoke({
            "text": proofread_text,
            "original_text": original_text
        }, config={"model": model_name})
        
        # 결과 텍스트 로깅
        corrected_text = result.content
        logger.info("===== Raw LLM Output for Contextual Start =====")
        logger.info(f"\n{corrected_text[:1000]}...\n")
        logger.info("===== Raw LLM Output for Contextual End =====")
        
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
                # 페이지 텍스트에서 페이지 마커 제거
                cleaned_page_text = re.sub(r'\[Page \d+\]\s*', '', page_text).strip()
                pages.append({
                    'pageKey': page_key,
                    'text': cleaned_page_text
                })
                logger.debug(f"페이지 {page_key} 처리됨, 텍스트 길이: {len(cleaned_page_text)}")
            except ValueError:
                logger.error(f"페이지 키 변환 오류: {page_key_str}")
        
        # 누락된 페이지가 있는지 확인
        missing_page_keys = set(all_page_keys) - processed_page_keys
        if missing_page_keys:
            logger.warning(f"LLM 결과에서 누락된 페이지 키가 있습니다: {missing_page_keys}")
            for page_key in missing_page_keys:
                # 이전 단계 결과에서 페이지 찾기
                proofread_page = next((p for p in current_state.candidate_proofread if p.get('pageKey') == page_key), None)
                if proofread_page:
                    # 이전 단계 결과 사용 (페이지 마커 제거)
                    proofread_text = proofread_page['text']
                    cleaned_proofread_text = re.sub(r'\[Page \d+\]\s*', '', proofread_text).strip()
                    pages.append({
                        'pageKey': page_key,
                        'text': cleaned_proofread_text
                    })
                    logger.info(f"페이지 {page_key}를 이전 단계 결과로 추가했습니다: {cleaned_proofread_text[:50]}...")
                else:
                    # 원본 페이지 찾기
                    original_page = next((p for p in current_state.pages if p.pageKey == page_key), None)
                    if original_page:
                        # 원본 텍스트 사용 (페이지 마커 제거)
                        original_text_content = ' '.join([t.text for t in original_page.texts])
                        cleaned_original_text = re.sub(r'\[Page \d+\]\s*', '', original_text_content).strip()
                        pages.append({
                            'pageKey': page_key,
                            'text': cleaned_original_text
                        })
                        logger.info(f"페이지 {page_key}를 원본 텍스트로 추가했습니다: {cleaned_original_text[:50]}...")
                    else:
                        # 비어있는 페이지인 경우 비어있는 배열 추가
                        pages.append({
                        'pageKey': page_key,
                        'text': ''
                        })
                        logger.info(f"페이지 {page_key}를 빈 텍스트로 추가했습니다.")
        
        # 페이지 키 기준으로 정렬
        pages.sort(key=lambda x: x['pageKey'])
        
        # 최종 로깅
        logger.info(f"최종 처리된 페이지 수: {len(pages)}, 필요한 페이지 수: {len(all_page_keys)}")
        for page in pages:
            logger.info(f"  PageKey: {page.get('pageKey')}, Text length: {len(page.get('text', ''))}")
        
        current_state.candidate_contextual = pages
        logger.info(f"최종 처리된 페이지 수: {len(pages)}")
        
        return {"state": current_state.model_dump()}, "contextual"

    except Exception as e:
        logger.error(f"문맥 처리 에이전트 오류 발생: {str(e)}", exc_info=True)
        logger.error(f"입력 상태: {state}")
        raise
