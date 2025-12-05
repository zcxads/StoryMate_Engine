import re
import asyncio
import json
from typing import Dict, Any, List

from langsmith.run_helpers import traceable

from app.utils.logger.setup import setup_logger
from app.prompts.language.translation import (
    get_translation_prompt_config,
    get_language_names,
    get_json_array_translation_prompt
)
from app.utils.language.generator import language_generator

# 로거 설정
logger = setup_logger('translation', 'logs/translation')

# 번역 프롬프트에서 언어 이름 가져오기
LANGUAGE_NAMES = get_language_names()

def extract_book_content(llm_text_data: List[Dict[str, Any]]) -> str:
    """책 전체 내용을 추출하여 단일 문자열로 반환"""
    full_content = []

    # 페이지별로 텍스트 정리
    for page in llm_text_data:
        page_text = []

        # 새로운 구조: 직접 text 필드가 있는 경우
        if "text" in page:
            text = page.get("text", "").strip()
            if text:
                # 번역 품질을 위해 원본 줄바꿈/목록 구조 유지
                page_text.append(text)

        # 기존 구조: texts 배열이 있는 경우 (하위 호환성)
        elif "texts" in page:
            for text_item in page.get("texts", []):
                text = text_item.get("text", "").strip()
                if text:
                    # 번역 품질을 위해 원본 줄바꿈/목록 구조 유지
                    page_text.append(text)

        # 페이지 내용 병합
        if page_text:
            full_content.append("\n".join(page_text))

    # 전체 내용 병합
    return "\n\n".join(full_content)

def get_translation_prompt(target_language: str) -> str:
    """타겟 언어에 맞는 번역 프롬프트 생성"""
    prompt_config = get_translation_prompt_config(target_language)
    return prompt_config["template"]

async def translate_with_unified_model(content: str, target_language: str, model_name: str = "gemini") -> str:
    """통합 언어 모델을 사용하여 텍스트 번역 - 청크 기반"""
    # 텍스트가 너무 길면 청크로 분할하여 번역
    max_chunk_size = 12000  # 안전한 청크 크기

    if len(content) <= max_chunk_size:
        # 짧은 텍스트는 한 번에 번역
        return await translate_single_chunk(content, target_language, model_name)

    # 긴 텍스트는 청크로 분할하여 번역
    logger.info(f"Text too long ({len(content)} chars), splitting into chunks")
    chunks = split_text_into_chunks(content, max_chunk_size)
    logger.info(f"Split into {len(chunks)} chunks")

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
        try:
            translated_chunk = await translate_single_chunk(chunk, target_language, model_name)
            translated_chunks.append(translated_chunk)
            logger.debug(f"Chunk {i+1} translated successfully")
        except Exception as e:
            logger.error(f"Failed to translate chunk {i+1}: {str(e)}")
            # 실패한 청크는 원본 유지
            translated_chunks.append(chunk)

    # 번역된 청크들을 합치기
    result = "\n\n".join(translated_chunks)
    logger.info(f"Combined translation complete: {len(result)} chars")
    return result


async def translate_single_chunk(content: str, target_language: str, model_name: str = "gemini") -> str:
    """단일 청크 번역"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # 프롬프트 생성
            prompt_template = get_translation_prompt(target_language)
            formatted_prompt = prompt_template.format(text=content)

            # 모델 호출
            response = await language_generator.ainvoke(
                formatted_prompt,
                config={"model": model_name}
            )

            # 응답에서 텍스트 추출
            translated_text = response.content.strip()
            return translated_text

        except Exception as e:
            logger.error(f"번역 중 오류 (시도 {retry_count+1}): {str(e)}", exc_info=True)
            retry_count += 1
            if retry_count >= max_retries:
                logger.error("최대 재시도 횟수 도달. 원본 내용 반환.")
                return content  # 오류 시 원본 반환
            await asyncio.sleep(1)  # 재시도 전 잠시 대기

def split_text_into_chunks(text: str, max_chars: int = 12000) -> List[str]:
    """텍스트를 번역에 적합한 크기의 청크로 분할"""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        # 현재 청크에 단락을 추가했을 때 크기 확인
        test_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph

        if len(test_chunk) <= max_chars:
            current_chunk = test_chunk
        else:
            # 현재 청크가 있으면 저장
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # 단일 단락이 너무 긴 경우 문장 단위로 분할
                sentences = paragraph.split(". ")
                temp_chunk = ""
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if not sentence.endswith(".") and not sentence.endswith("!") and not sentence.endswith("?"):
                        sentence += "."

                    test_sentence_chunk = temp_chunk + (" " if temp_chunk else "") + sentence
                    if len(test_sentence_chunk) <= max_chars:
                        temp_chunk = test_sentence_chunk
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = sentence

                if temp_chunk:
                    current_chunk = temp_chunk

    # 마지막 청크 저장
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def map_translations_to_original(original_book: List[Dict[str, Any]], original_content: str, translated_content: str) -> List[Dict[str, Any]]:
    """번역된 내용을 원본 구조에 매핑 - 개선된 순서 기반 매핑"""
    logger.info("Starting improved mapping process")
    
    # 원본 문장과 번역된 문장 분리
    original_paragraphs = original_content.split("\n\n")
    translated_paragraphs = translated_content.split("\n\n")
    
    # 단락 수가 일치하지 않아도 자르지 않고 진행 (순서 폴백과 보조 분할이 처리)
    if len(original_paragraphs) != len(translated_paragraphs):
        logger.warning(f"Paragraph count mismatch: Original={len(original_paragraphs)}, Translated={len(translated_paragraphs)} - proceeding without truncation")
    
    # 원본 책 구조 복사 (새로운 구조와 기존 구조 모두 지원)
    result_book = []
    for page in original_book:
        # pageKey 값이 있으면 보존, 없으면 0으로 설정
        new_page = {"pageKey": page.get("pageKey", 0)}
        
        # 새로운 구조: 직접 text 필드가 있는 경우
        if "text" in page:
            new_page["text"] = page.get("text", "")
        # 기존 구조: texts 배열이 있는 경우
        elif "texts" in page:
            new_page["texts"] = []
            for text_item in page.get("texts", []):
                new_text_item = {"text": text_item.get("text", "")}
                new_page["texts"].append(new_text_item)
        
        result_book.append(new_page)
    
    # 모든 원본 문장을 순서대로 수집
    all_original_sentences = []
    for paragraph in original_paragraphs:
        sentences = paragraph.split("\n")
        for sentence in sentences:
            if sentence.strip():
                all_original_sentences.append(sentence.strip())
    
    # 모든 번역된 문장을 순서대로 수집 (1차: 줄 기준)
    all_translated_sentences = []
    for translated_paragraph in translated_paragraphs:
        sentences = translated_paragraph.split("\n")
        for sentence in sentences:
            if sentence.strip():
                all_translated_sentences.append(sentence.strip())

    # 번역 문장이 턱없이 적을 경우 보조 분할 적용 (2차: 문장부호 기준)
    if len(all_translated_sentences) < len(all_original_sentences):
        # 전체 번역 텍스트에서 문장부호 기준으로 세분화 시도
        # 영어/한글/중문 문장부호 포함: . ! ? … 。 ！ ？
        punctuation_split_regex = r'(?<=[\.!?…。！？])\s+'
        refined_sentences = []
        translated_whole = translated_content.replace('\n', ' ').strip()
        for chunk in re.split(punctuation_split_regex, translated_whole):
            chunk = chunk.strip()
            if chunk:
                refined_sentences.append(chunk)
        # 보조 분할 결과가 더 많으면 교체
        if len(refined_sentences) > len(all_translated_sentences):
            logger.info(f"Refined translated sentences using punctuation split: {len(refined_sentences)} (prev {len(all_translated_sentences)})")
            all_translated_sentences = refined_sentences
    
    logger.info(f"Original sentences: {len(all_original_sentences)}, Translated sentences: {len(all_translated_sentences)}")
    
    # 문장 수 맞추기 (매핑 1단계에서만 사용; 원본/번역 자체는 truncate 하지 않음)
    min_sentences = min(len(all_original_sentences), len(all_translated_sentences))
    if min_sentences < len(all_original_sentences):
        logger.warning(f"Insufficient translated sentences: original {len(all_original_sentences)} > translated {len(all_translated_sentences)}")
    if min_sentences < len(all_translated_sentences):
        logger.warning(f"Excess translated sentences: translated {len(all_translated_sentences)} > original {len(all_original_sentences)}")
    
    # 3단계: 원본 구조에 번역 적용 - 비율 기반 매핑
    mapped_count = 0
    total_original = len(all_original_sentences)
    total_translated = len(all_translated_sentences)

    # 비율 계산 (번역 문장 수 / 원본 문장 수)
    translation_ratio = total_translated / total_original if total_original > 0 else 1
    logger.info(f"Translation ratio: {translation_ratio:.3f} ({total_translated}/{total_original})")

    current_translated_idx = 0

    for page_idx, page in enumerate(original_book):
        # 새로운 구조: 직접 text 필드가 있는 경우
        if "text" in page:
            original_text = page.get("text", "")
            original_lines = [ln for ln in original_text.split("\n") if ln.strip() != ""]

            if len(original_lines) > 0:
                # 남은 번역 문장 수 확인
                remaining_translated = total_translated - current_translated_idx

                if remaining_translated > 0:
                    # 이 텍스트 블록에 할당할 번역 문장 수 계산
                    expected_translated = max(1, round(len(original_lines) * translation_ratio))
                    actual_assigned = min(remaining_translated, expected_translated)

                    end_idx = current_translated_idx + actual_assigned
                    assigned = all_translated_sentences[current_translated_idx:end_idx]
                    current_translated_idx = end_idx

                    result_book[page_idx]["text"] = "\n".join(assigned)
                    mapped_count += 1
                    logger.debug(f"✅ 비율 매핑 (text): orig_lines={len(original_lines)}, assigned={len(assigned)}, remaining={remaining_translated}")
                else:
                    # 번역 문장이 모두 소진된 경우 해당 텍스트 블록 제거 (빈 문자열 할당)
                    result_book[page_idx]["text"] = ""
                    logger.debug(f"⚠️ 번역 문장 소진 - 텍스트 블록 제거 (text page {page_idx})")
            else:
                result_book[page_idx]["text"] = original_text

        # 기존 구조: texts 배열이 있는 경우
        elif "texts" in page:
            for text_idx, text_item in enumerate(page.get("texts", [])):
                original_text = text_item.get("text", "")
                original_lines = [ln for ln in original_text.split("\n") if ln.strip() != ""]

                if len(original_lines) > 0:
                    # 남은 번역 문장 수 확인
                    remaining_translated = total_translated - current_translated_idx

                    if remaining_translated > 0:
                        # 이 텍스트 블록에 할당할 번역 문장 수 계산
                        expected_translated = max(1, round(len(original_lines) * translation_ratio))
                        # 남은 문장이 적으면 모두 할당
                        actual_assigned = min(remaining_translated, expected_translated)

                        # 마지막 몇 개 블록이면 남은 문장을 더 관대하게 할당
                        if remaining_translated <= 3:
                            actual_assigned = remaining_translated

                        end_idx = current_translated_idx + actual_assigned
                        assigned = all_translated_sentences[current_translated_idx:end_idx]
                        current_translated_idx = end_idx

                        result_book[page_idx]["texts"][text_idx]["text"] = "\n".join(assigned)
                        mapped_count += 1
                        logger.debug(f"✅ 개선 매핑 (texts): orig_lines={len(original_lines)}, assigned={len(assigned)}, remaining={remaining_translated}")
                    else:
                        # 번역 문장이 모두 소진된 경우 해당 텍스트 블록 제거 (빈 문자열 할당)
                        result_book[page_idx]["texts"][text_idx]["text"] = ""
                        logger.debug(f"⚠️ 번역 문장 소진 - 텍스트 블록 제거 (texts page {page_idx} idx {text_idx})")

    # 남은 번역 문장이 있으면 경고 로그
    remaining_sentences = total_translated - current_translated_idx
    if remaining_sentences > 0:
        logger.warning(f"Unused translated sentences: {remaining_sentences}/{total_translated} sentences not assigned")

    logger.info(f"Applied translations to {mapped_count} text items across {len(result_book)} pages (ratio-based mapping with {translation_ratio:.3f} ratio, used {current_translated_idx}/{total_translated} sentences)")
    return result_book

async def translate_with_index_mapping(original_llmText: List[Dict[str, Any]], target_language: str, model_name: str) -> List[Dict[str, Any]]:
    """
    JSON 배열 방식으로 전체 번역 후 입력 인덱스에 맞게 출력 (1:1 보장)

    Args:
        original_llmText: 원본 llmText 구조
        target_language: 목표 언어
        model_name: 사용할 모델

    Returns:
        번역된 llmText (입력과 동일한 인덱스 구조)
    """
    # 1. 모든 텍스트 추출
    all_texts = []
    text_count_per_page = []

    for page in original_llmText:
        if "texts" in page:
            texts = page.get("texts", [])
            text_count_per_page.append(len(texts))
            for text_item in texts:
                all_texts.append(text_item.get("text", "").strip())
        elif "text" in page:
            text_count_per_page.append(1)
            all_texts.append(page.get("text", "").strip())

    total_texts = len(all_texts)
    logger.info(f"Total texts to translate: {total_texts}")
    logger.info(f"Pages: {len(original_llmText)}, Texts per page: {text_count_per_page}")

    # 2. JSON 배열로 입력 구성
    input_json = json.dumps(all_texts, ensure_ascii=False, indent=2)

    # 3. JSON 배열 번역 프롬프트 (prompts 모듈에서 가져오기)
    enhanced_prompt = get_json_array_translation_prompt(target_language, total_texts, input_json)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Translation attempt {attempt + 1}/{max_retries}")

            response = await language_generator.ainvoke(
                enhanced_prompt,
                config={"model": model_name}
            )

            result = response.content.strip()

            # 원본 응답 로그
            logger.info(f"===== Raw LLM Response =====")
            logger.info(f"{result[:200]}\n\n...\n\n{result[-200:]}")

            # JSON 추출 (마크다운 코드블록 제거)
            if result.startswith("```"):
                # ```json ... ``` 또는 ``` ... ``` 형태 처리
                result = re.sub(r'^```(?:json)?\s*\n', '', result)
                result = re.sub(r'\n```\s*$', '', result)
                result = result.strip()
                logger.info("Removed markdown code block wrapper")

            # JSON 파싱 전 로그
            translated_array = json.loads(result)
            logger.info(f"JSON parsing successful: {len(translated_array)} items")

            # 배열 검증
            if not isinstance(translated_array, list):
                raise ValueError(f"Output is not a list: {type(translated_array)}")

            if len(translated_array) != total_texts:
                logger.error(f"Count mismatch: expected {total_texts}, got {len(translated_array)}")
                if attempt < max_retries - 1:
                    logger.info("Retrying...")
                    continue
                else:
                    raise ValueError(f"After {max_retries} attempts, still got {len(translated_array)} items instead of {total_texts}")

            logger.info(f"✅ Translation successful: {len(translated_array)} items")

            # 4. 원본 구조에 맞게 재조립
            result_llmText = []
            text_idx = 0

            for page_idx, page in enumerate(original_llmText):
                page_key = page.get("pageKey", page_idx)

                if "texts" in page:
                    page_text_count = text_count_per_page[page_idx]
                    translated_page_texts = []

                    for i in range(page_text_count):
                        translated_text = translated_array[text_idx] if text_idx < len(translated_array) else ""
                        translated_page_texts.append({"text": translated_text})
                        text_idx += 1

                    result_llmText.append({
                        "pageKey": page_key,
                        "texts": translated_page_texts
                    })

                    logger.debug(f"Page {page_key}: reconstructed with {len(translated_page_texts)} texts")

                elif "text" in page:
                    translated_text = translated_array[text_idx] if text_idx < len(translated_array) else ""
                    result_llmText.append({
                        "pageKey": page_key,
                        "text": translated_text
                    })
                    text_idx += 1

            logger.info(f"Successfully reconstructed {len(result_llmText)} pages")
            return result_llmText

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error (attempt {attempt + 1}): {str(e)}")
            logger.error(f"Raw output: {result[:500]}...")
            if attempt < max_retries - 1:
                logger.info("Retrying...")
                await asyncio.sleep(1)
            else:
                raise Exception(f"Failed to parse JSON after {max_retries} attempts: {str(e)}")

        except Exception as e:
            logger.error(f"Translation error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info("Retrying...")
                await asyncio.sleep(1)
            else:
                raise

    raise Exception("Translation failed after all retries")

@traceable(run_type="chain")
async def translation_agent(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """텍스트 번역 에이전트 - 모델 1회 호출로 전체 번역 후 인덱스 매칭"""
    try:
        logger.info("Starting translation process (single model call with index mapping)")
        state = state.get("state", state)

        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model")

        # 타겟 언어 및 입력 텍스트 추출
        target_language = state.get("target")
        logger.info(f"Target language: {target_language}, using model: {model_name}")

        # 원본 llm_text 데이터 보존
        original_llmText = state.get("llmText", [])

        # 입력 인덱스 카운트
        input_text_count = sum(
            len(page.get("texts", [])) if "texts" in page else 1
            for page in original_llmText
        )
        logger.info(f"Input: {len(original_llmText)} pages, {input_text_count} total texts")

        # 번역 API 호출 = 번역 의도 명확 → 번역 필요 여부 확인 불필요
        # 불필요한 LLM 호출 제거 (최대 9번 호출 가능했던 병목 제거)
        logger.info("Starting translation process...")
        result_llmText = await translate_with_index_mapping(original_llmText, target_language, model_name)

        # 출력 인덱스 카운트
        output_text_count = sum(
            len(page.get("texts", [])) if "texts" in page else 1
            for page in result_llmText
        )
        logger.info(f"Output: {len(result_llmText)} pages, {output_text_count} total texts")

        # 인덱스 일치 검증
        if input_text_count != output_text_count:
            logger.error(f"❌ TEXT COUNT MISMATCH: input {input_text_count} != output {output_text_count}")
        else:
            logger.info(f"✅ TEXT COUNT MATCH: {input_text_count} texts")

        # 페이지별 검증
        for page_idx, (orig_page, result_page) in enumerate(zip(original_llmText, result_llmText)):
            if "texts" in orig_page and "texts" in result_page:
                orig_count = len(orig_page.get("texts", []))
                result_count = len(result_page.get("texts", []))
                if orig_count != result_count:
                    logger.error(f"❌ Page {page_idx} mismatch: input {orig_count} != output {result_count}")
                else:
                    logger.debug(f"✅ Page {page_idx} match: {orig_count} texts")

        # 상태 업데이트
        state["llmText"] = result_llmText

        # 샘플 확인
        if result_llmText and len(result_llmText) > 0:
            if "texts" in result_llmText[0] and len(result_llmText[0]["texts"]) > 0:
                logger.info(f"Sample translated text: {result_llmText[0]['texts'][0]['text'][:100]}...")
            elif "text" in result_llmText[0]:
                logger.info(f"Sample translated text: {result_llmText[0]['text'][:100]}...")

        logger.info("Translation completed with index matching")

        return {"state": state}

    except Exception as e:
        logger.error(f"Error in translation agent: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return {"state": state}
