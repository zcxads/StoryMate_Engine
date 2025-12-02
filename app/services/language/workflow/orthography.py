import os
import json
import logging
import re
import asyncio
from typing import List, Dict, Any

from app.models.state import OrthographyState, Page, PageText
from app.core.config import settings
from app.utils.logger.setup import setup_logger
from app.services.language.orthography.proofreading import proofreading_agent_per_page
from app.services.language.orthography.contextual import contextual_agent_per_page
from app.services.language.language_detection.detector import detect_language_with_ai

logger = setup_logger("orthography")

def detect_table_structure(text: str, page_key: int = None) -> bool:
    """텍스트에서 테이블 구조를 감지합니다."""
    # 마크다운 테이블 패턴 감지
    markdown_table_pattern = r'\|.*\|.*\|'
    # 연속된 구분자 패턴 감지
    separator_pattern = r'[|\-]{3,}'

    has_markdown = bool(re.search(markdown_table_pattern, text))
    has_separator = bool(re.search(separator_pattern, text))

    is_table = has_markdown or has_separator

    # 디버깅: 어떤 패턴이 매칭되었는지 로깅
    if is_table and page_key is not None:
        matched_patterns = []
        if has_markdown:
            matched_patterns.append("마크다운테이블(|)")
            match = re.search(markdown_table_pattern, text)
            logger.debug(f"  매칭된 부분: {text[max(0, match.start()-20):match.end()+20]}")
        if has_separator:
            matched_patterns.append("구분자(---)")
            match = re.search(separator_pattern, text)
            logger.debug(f"  매칭된 부분: {text[max(0, match.start()-20):match.end()+20]}")
        logger.info(f"페이지 {page_key} 테이블 패턴 감지: {', '.join(matched_patterns)}")

    return is_table

def combine_table_pages(pages: List[Page]) -> List[Page]:
    """테이블이 여러 페이지에 걸쳐 있는 경우 결합합니다."""
    if not pages:
        return pages
    
    combined_pages = []
    current_table_pages = []
    
    for page in pages:
        page_text = ' '.join([t.text for t in page.texts])
        
        # 테이블 구조 감지
        if detect_table_structure(page_text):
            current_table_pages.append(page)
        else:
            # 테이블이 끝났거나 시작되지 않은 경우
            if current_table_pages:
                # 여러 페이지에 걸친 테이블을 하나로 결합
                if len(current_table_pages) > 1:
                    combined_text = []
                    for table_page in current_table_pages:
                        combined_text.extend([t.text for t in table_page.texts])
                    
                    # 첫 번째 페이지에 모든 텍스트 결합
                    first_page = current_table_pages[0]
                    first_page.texts = [PageText(text=line) for line in combined_text]
                    combined_pages.append(first_page)
                    
                    logger.info(f"테이블 페이지 {[p.pageKey for p in current_table_pages]} 결합됨")
                else:
                    # 단일 페이지 테이블
                    combined_pages.append(current_table_pages[0])
                
                current_table_pages = []
            
            # 일반 페이지 추가
            combined_pages.append(page)
    
    # 마지막에 남은 테이블 페이지 처리
    if current_table_pages:
        if len(current_table_pages) > 1:
            combined_text = []
            for table_page in current_table_pages:
                combined_text.extend([t.text for t in table_page.texts])
            
            first_page = current_table_pages[0]
            first_page.texts = [PageText(text=line) for line in combined_text]
            combined_pages.append(first_page)
            
            logger.info(f"마지막 테이블 페이지 {[p.pageKey for p in current_table_pages]} 결합됨")
        else:
            combined_pages.append(current_table_pages[0])
    
    return combined_pages

async def process_page_orthography(page: Page, language: str = "ko", model: str = settings.llm_text_processing_model) -> dict:
    """개별 페이지에 대한 텍스트 교정 처리

    Args:
        page: 처리할 페이지
        language: 언어 코드 (ko, en, ja, zh 등)
        model: 사용할 LLM 모델
    """
    try:
        logger.info(f"페이지 {page.pageKey} 처리 시작 (언어: {language})")

        # 페이지 텍스트 결합
        page_text = ' '.join([t.text for t in page.texts])

        # 페이지 마커 제거 (개별 페이지 처리에서는 불필요)
        cleaned_page_text = re.sub(r'\[Page \d+\]\s*', '', page_text).strip()

        # 테이블 구조 감지 (원본 텍스트 기준)
        has_table = detect_table_structure(cleaned_page_text, page_key=page.pageKey)
        if has_table:
            logger.info(f"페이지 {page.pageKey}에서 원본 텍스트에서 테이블 구조 감지됨")

        # 1. Proofreading 단계 (개별 페이지) - 언어 전달
        proofread_result = await proofreading_agent_per_page(
            cleaned_page_text, page.pageKey, language=language, model=model
        )

        # 2. Contextual 단계 (개별 페이지) - 언어 전달
        contextual_result = await contextual_agent_per_page(
            proofread_result, cleaned_page_text, page.pageKey, language=language, model=model
        )

        logger.info(f"페이지 {page.pageKey} 처리 완료")
        return {
            "pageKey": page.pageKey,
            "text": contextual_result,
            "status": "success",
            "has_table": has_table
        }

    except Exception as e:
        logger.error(f"페이지 {page.pageKey} 처리 중 오류 발생: {str(e)}", exc_info=True)
        # 오류가 발생한 경우 원본 텍스트를 반환 (페이지 마커 제거)
        original_text = ' '.join([t.text for t in page.texts])
        cleaned_original_text = re.sub(r'\[Page \d+\]\s*', '', original_text).strip()
        return {
            "pageKey": page.pageKey,
            "text": cleaned_original_text,
            "status": "error",
            "error": str(e),
            "has_table": False
        }

async def process_orthography_workflow(state: OrthographyState, model: str = settings.llm_text_processing_model) -> dict:
    """텍스트 교정 워크플로우 실행 (페이지별 병렬 처리)"""
    try:
        logger.info(f"전체 {len(state.pages)} 페이지 처리 시작")

        # 언어 감지를 위해 모든 텍스트 수집
        all_text = ""
        for page in state.pages:
            for text_item in page.texts:
                all_text += text_item.text + " "

        # AI 기반 언어 감지 수행
        detected_language = "ko"  # 기본값
        if all_text.strip():
            try:
                detection_result = await detect_language_with_ai(all_text.strip(), model)
                detected_language = detection_result.get("primary_language")
                confidence = detection_result.get("confidence", 0.0)
                logger.info(f"AI 언어 감지 결과: {detected_language} - 신뢰도: {confidence:.3f}")
            except Exception as e:
                logger.warning(f"AI 언어 감지 실패, 기본값(en) 사용: {e}")

        # 테이블 페이지 결합 (옵션)
        # processed_pages = combine_table_pages(state.pages)
        # logger.info(f"테이블 결합 후 {len(processed_pages)} 페이지")

        # 현재는 기본 처리 방식 사용
        processed_pages = state.pages

        # 각 페이지를 병렬로 처리 (감지된 언어 전달)
        tasks = [
            process_page_orthography(page, language=detected_language, model=model)
            for page in processed_pages
        ]

        # 병렬 처리 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        corrected_pages = []
        error_count = 0
        table_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"페이지 처리 중 예외 발생: {str(result)}")
                error_count += 1
                continue
                
            if result["status"] == "error":
                error_count += 1
                logger.warning(f"페이지 {result['pageKey']} 처리 실패, 원본 텍스트 사용")
            
            if result.get("has_table", False):
                table_count += 1
                logger.info(f"페이지 {result['pageKey']}에서 테이블 처리됨")
            
            corrected_pages.append(result)
        
        # 페이지 키 기준으로 정렬
        corrected_pages.sort(key=lambda x: x["pageKey"])
        
        logger.info(f"전체 {len(corrected_pages)} 페이지 처리 완료, 오류 {error_count}개, 테이블 {table_count}개")
        
        # 최종 결과 구성
        new_corrected_pages = []
        for page in corrected_pages:
            page_text = page["text"].strip()
            
            if not page_text:
                logger.info(f"페이지 {page['pageKey']} 텍스트가 비어있음 - 원본 텍스트 확인")
                # 원본 페이지에서 텍스트가 있었는지 확인
                original_page = next((p for p in state.pages if p.pageKey == page["pageKey"]), None)
                if original_page and original_page.texts and any(t.text.strip() for t in original_page.texts):
                    # 원본에 텍스트가 있었다면 원본 사용
                    original_texts = [{"text": t.text.strip()} for t in original_page.texts if t.text.strip()]
                    if original_texts:
                        new_page = {"pageKey": page["pageKey"], "texts": original_texts}
                        logger.warning(f"페이지 {page['pageKey']} 처리 실패, 원본 텍스트 사용")
                    else:
                        # 원본도 비어있다면 빈 페이지로 처리
                        new_page = {"pageKey": page["pageKey"], "texts": []}
                        logger.info(f"페이지 {page['pageKey']} 원본도 비어있음, 빈 페이지로 처리")
                else:
                    # 원본부터 비어있던 페이지
                    new_page = {"pageKey": page["pageKey"], "texts": []}
                    logger.info(f"페이지 {page['pageKey']} 원본부터 비어있음")
            else:
                # AI 처리 결과를 기준으로 테이블 여부 재검사
                is_table = detect_table_structure(page_text, page_key=page['pageKey'])
                logger.info(f"페이지 {page['pageKey']} 테이블 감지: {is_table}")

                if is_table:
                    # 테이블은 줄바꿈을 기준으로 분리
                    sentences = [line.strip() for line in page_text.split('\n') if line.strip()]
                    logger.info(f"페이지 {page['pageKey']} 테이블 모드: {len(sentences)}개 라인으로 분리")
                else:
                    # 일반 텍스트는 줄바꿈 기준으로 간단 분리 (LLM 호출 제거)
                    # 교정된 텍스트는 이미 LLM이 처리했으므로 추가 분리 불필요
                    sentences = [line.strip() for line in page_text.split('\n') if line.strip()]
                    if not sentences:
                        # 줄바꿈이 없으면 전체를 하나의 문장으로
                        sentences = [page_text]
                    logger.info(f"페이지 {page['pageKey']} 줄바꿈 기준 분리: {len(sentences)}개 라인")

                # 분리 결과가 비어 있는지 확인
                if not any(s.strip() for s in sentences):
                    logger.warning(f"페이지 {page['pageKey']} 분리 결과가 비어있음")
                    # 원본 텍스트 사용
                    if page_text.strip() == '[Blank]':
                        sentences = []
                    else:
                        sentences = [page_text]

                new_page = {
                    "pageKey": page["pageKey"],
                    "texts": [{"text": sentence} for sentence in sentences if sentence.strip()]
                }
            
            new_corrected_pages.append(new_page)
        
        # 최종 검증
        expected_page_keys = set(page.pageKey for page in state.pages)
        actual_page_keys = set(page["pageKey"] for page in new_corrected_pages)
        
        if expected_page_keys != actual_page_keys:
            missing_keys = expected_page_keys - actual_page_keys
            logger.info(f"빈 텍스트로 인해 제외된 페이지 키: {missing_keys}")
            
            # 누락된 페이지 추가 (빈 페이지는 제외)
            for page_key in missing_keys:
                original_page = next((p for p in state.pages if p.pageKey == page_key), None)
                if original_page and original_page.texts:
                    original_texts = [{"text": t.text} for t in original_page.texts if t.text.strip()]
                    if original_texts:
                        new_page = {
                            "pageKey": page_key,
                            "texts": original_texts
                        }
                        new_corrected_pages.append(new_page)
                        logger.info(f"누락된 페이지 {page_key} 추가됨 (텍스트 {len(original_texts)}개)")
                    else:
                        logger.info(f"누락된 페이지 {page_key}는 빈 페이지로 결과에서 제외")
                else:
                    logger.info(f"누락된 페이지 {page_key}는 원본부터 비어있어 결과에서 제외")
            
            # 다시 정렬
            new_corrected_pages.sort(key=lambda x: x["pageKey"])
        
        logger.info(f"최종 처리된 페이지 수: {len(new_corrected_pages)}")
        for page in new_corrected_pages:
            logger.info(f"  PageKey: {page['pageKey']}, Texts: {len(page['texts'])}")

        # 언어 감지는 이미 입력 단계에서 수행되었으므로 재사용
        # 불필요한 중복 LLM 호출 제거
        return {
            "llmText": new_corrected_pages,
            "detected_language": detected_language  # 입력 단계의 언어 감지 결과 사용
        }
        
    except Exception as e:
        logger.error(f"텍스트 교정 워크플로우 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "llmText": [],
            "detected_language": None
        }

async def process_orthography_workflow_wrapper(request_data) -> dict:
    """텍스트 교정 워크플로우 래퍼 - 문장 분리 최적화"""
    try:
        # model 필드 추출
        model = request_data.get("model", settings.llm_text_processing_model) if isinstance(request_data, dict) else getattr(request_data, "model", settings.llm_text_processing_model)

        request_pages = request_data["pages"] if isinstance(request_data, dict) else request_data.pages

        # 페이지 데이터를 그대로 사용 (문장 분리 제거)
        # 교정 에이전트가 자체적으로 문장을 처리하므로 사전 분리 불필요
        pages = []
        for page in request_pages:
            text_content = page["text"] if isinstance(page, dict) else page.text
            page_key = page["pageKey"] if isinstance(page, dict) else page.pageKey

            # 원본 텍스트를 단일 항목으로 유지 (문장 분리하지 않음)
            texts = [PageText(text=text_content)]
            pages.append(Page(pageKey=page_key, texts=texts))

        logger.info(f"교정 워크플로우 실행 - 총 {len(pages)} 페이지 (원본 구조 유지)")

        state = OrthographyState(pages=pages)
        result = await process_orthography_workflow(state, model=model)

        return result

    except Exception as e:
        logger.error(f"텍스트 교정 워크플로우 래퍼 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "llmText": [],
            "detected_language": None
        }
