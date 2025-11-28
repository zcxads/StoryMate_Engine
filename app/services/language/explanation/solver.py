"""
이미지 기반 문제 해결 서비스
"""

import base64
import re
import os
import json
from typing import Tuple, Dict, Any, Optional

from app.prompts.language.explanation.solver import create_explanation_prompt
from app.prompts.language.explanation.choice_extractor import create_choice_extraction_prompt
from app.utils.logger.setup import setup_logger
from app.core.config import settings
from app.utils.language.generator import call_llm

# 로거 설정
logger = setup_logger('explanation_solver', 'logs/services')

async def extract_multiple_choice_options(image_base64: str, model: str, language: str) -> Optional[Dict[str, Any]]:
    """
    이미지에서 객관식 선택지를 추출합니다.

    Args:
        image_base64: Base64로 인코딩된 이미지 데이터
        model: 사용할 언어 모델
        language: 응답 언어

    Returns:
        Optional[Dict[str, Any]]: 선택지 정보 또는 None (객관식이 아닌 경우)
    """
    try:
        logger.info("객관식 선택지 추출 시작...")

        # 선택지 추출 프롬프트 가져오기
        prompt_text = create_choice_extraction_prompt(language)

        # Base64 이미지 데이터 처리
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        response = await call_llm(prompt=messages, model=model)
        result_text = response.content

        logger.info(f"선택지 추출 응답: {result_text}")

        # JSON 파싱
        cleaned_text = result_text.strip()

        # JSON 코드 블록 제거
        json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_match = re.search(r'(\{.*\}|null)', cleaned_text, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = cleaned_text

        # null 체크
        if json_str.lower() == 'null':
            logger.info("객관식 문제가 아닙니다.")
            return None

        parsed_options = json.loads(json_str)

        # 유효성 검증
        if parsed_options and 'options' in parsed_options and isinstance(parsed_options['options'], list):
            logger.info(f"객관식 선택지 추출 완료: {len(parsed_options['options'])}개")
            return parsed_options
        else:
            logger.info("객관식 선택지가 없습니다.")
            return None

    except Exception as e:
        logger.warning(f"선택지 추출 실패: {str(e)}, 객관식이 아닌 것으로 간주")
        return None


def map_answer_to_option(answer_text: str, options: Dict[str, Any]) -> Optional[int]:
    """
    도출된 정답을 선택지에 매핑하여 선택지 번호를 반환합니다.

    Args:
        answer_text: 문제 풀이에서 도출된 정답 텍스트
        options: extract_multiple_choice_options에서 반환된 선택지 정보

    Returns:
        Optional[int]: 매칭된 선택지 번호 또는 None
    """
    if not options or 'options' not in options:
        return None

    # 정답 텍스트 정규화 (공백, 특수문자 제거)
    normalized_answer = re.sub(r'[^\w\./\-]', '', answer_text.lower().strip())

    logger.info(f"정답 매핑 시작 - 정규화된 정답: '{normalized_answer}'")

    best_match = None
    best_match_score = 0

    for option in options['options']:
        option_value = str(option.get('value', ''))
        option_number = option.get('number')

        # 선택지 값 정규화
        normalized_option = re.sub(r'[^\w\./\-]', '', option_value.lower().strip())

        logger.info(f"선택지 {option_number} 비교: '{normalized_option}'")

        # 완전 일치 확인
        if normalized_answer == normalized_option:
            logger.info(f"✅ 완전 일치: 선택지 {option_number}")
            return option_number

        # 부분 일치 확인
        if normalized_answer in normalized_option or normalized_option in normalized_answer:
            match_score = len(set(normalized_answer) & set(normalized_option))
            if match_score > best_match_score:
                best_match = option_number
                best_match_score = match_score

    if best_match:
        logger.info(f"✅ 부분 일치: 선택지 {best_match} (점수: {best_match_score})")
        return best_match

    logger.warning(f"⚠️ 매칭되는 선택지를 찾을 수 없습니다.")
    return None


async def solve_problem_from_image(image_base64: str, model: str, language: str) -> Dict[str, Any]:
    """
    Base64로 인코딩된 이미지에서 문제를 분석하고 해결합니다.

    Args:
        image_base64: Base64로 인코딩된 이미지 데이터
        model: 사용할 언어 모델 (기본값: gpt-4o)
        language: 응답 언어 (기본값: ko - 한국어)

    Returns:
        Dict[str, Any]: 구조화된 응답 데이터
    """
    # 모델이 지정되지 않았거나 빈 문자열인 경우 기본값 사용
    if not model:
        model = settings.llm_for_explanation

    logger.info(f"문제 해결 시작 - 모델: {model}, 언어: {language}")

    try:
        # 1단계: 객관식 선택지 추출 시도
        logger.info("1단계: 객관식 선택지 추출 시도...")
        multiple_choice_options = await extract_multiple_choice_options(image_base64, model, language)

        # 2단계: 문제 풀이
        logger.info("2단계: 문제 풀이 시작...")
        prompt_text = create_explanation_prompt(language)

        logger.info("LLM 호출 준비...")

        # Base64 이미지 데이터 처리
        clean_image_base64 = image_base64
        if image_base64.startswith('data:image'):
            clean_image_base64 = image_base64.split(',')[1]

        # 이미지와 텍스트를 포함한 메시지 생성
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{clean_image_base64}"
                        }
                    }
                ]
            }
        ]

        logger.info("LLM 호출 시작...")

        response = await call_llm(
            prompt=messages,
            model=model
        )
        result_text = response.content

        logger.info(f"LLM 응답: {result_text}")

        # 빈 응답 체크
        if not result_text or result_text.strip() == "":
            logger.error("LLM이 빈 응답을 반환했습니다.")
            raise Exception("LLM 응답이 비어있습니다. 다시 시도해주세요.")

        # JSON 응답 파싱
        parsed_response = parse_and_clean_response(result_text, language)

        # 3단계: 객관식인 경우 정답을 선택지 번호로 매핑
        if multiple_choice_options:
            logger.info("3단계: 정답을 선택지 번호로 매핑...")
            original_answer = parsed_response.get('answer', '')
            option_number = map_answer_to_option(original_answer, multiple_choice_options)

            if option_number is not None:
                # 선택지 번호로 answer 교체
                parsed_response['answer'] = str(option_number)
                logger.info(f"✅ 정답이 선택지 {option_number}번으로 매핑되었습니다. (원본: {original_answer})")
            else:
                logger.warning(f"⚠️ 선택지 매핑 실패, 원본 정답 유지: {original_answer}")

        return parsed_response

    except Exception as e:
        raise e

def parse_and_clean_response(response_text: str, language: str) -> Dict[str, Any]:
    """
    LLM 응답을 파싱하고 정리합니다.
    
    Args:
        response_text: LLM의 응답 텍스트
        language: 응답 언어
    
    Returns:
        Dict[str, Any]: 정리된 응답 데이터
    """
    try:
        # 응답 텍스트 정리
        cleaned_text = response_text.strip()

        # 이중 중괄호를 단일 중괄호로 치환 (프롬프트에서 {{가 나온 경우 처리)
        cleaned_text = re.sub(r'^\{\{', '{', cleaned_text)
        cleaned_text = re.sub(r'\}\}$', '}', cleaned_text)
        
        # JSON 코드 블록 제거 (```json ... ```)
        json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 직접 JSON 형태 추출 시도 (배열과 객체 모두 지원)
            json_match = re.search(r'(\[.*\]|\{.*\})', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = cleaned_text

        # 추가 정리: 이중 중괄호 처리
        json_str = re.sub(r'^\{\{', '{', json_str)
        json_str = re.sub(r'\}\}$', '}', json_str)

        # JSON 파싱
        parsed_json = json.loads(json_str)

        # JSON 배열인 경우 첫 번째 요소 추출
        if isinstance(parsed_json, list) and len(parsed_json) > 0:
            parsed_json = parsed_json[0]
            logger.info(f"JSON 배열에서 첫 번째 요소 추출: {parsed_json}")

        # 응답 정리
        cleaned_response = clean_json_response(parsed_json, language)
        
        logger.info(f"JSON 파싱 및 정리 완료 - 언어: {language}")
        return cleaned_response
        
    except json.JSONDecodeError as e:
        # JSON 파싱 실패 = 에러 메시지 텍스트로 간주
        raise Exception(response_text.strip())
    except Exception as e:
        logger.info(f"응답 파싱 실패: {str(e)}")
        raise e

def clean_json_response(parsed_json: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    파싱된 JSON 응답을 정리합니다.
    키는 영어로 고정하고, 값의 내용만 언어별로 다르게 합니다.

    Args:
        parsed_json: 파싱된 JSON 데이터
        language: 응답 언어

    Returns:
        Dict[str, Any]: 정리된 응답 데이터

    Raises:
        Exception: 필수 필드(answer, solution, concepts)가 누락된 경우
    """
    # 각 필드별로 정리 (키는 항상 영어로 고정)
    cleaned_response = {}

    response_keys = ['answer', 'solution', 'concepts']

    # 정답 정리
    if response_keys[0] in parsed_json:
        raw_answer = str(parsed_json[response_keys[0]])
        cleaned_response["answer"] = clean_answer_text(raw_answer)

    # 풀이과정 정리
    if response_keys[1] in parsed_json:
        raw_solution = str(parsed_json[response_keys[1]])
        cleaned_response["solution"] = clean_solution_text(raw_solution)

    # 핵심개념 정리
    if response_keys[2] in parsed_json:
        raw_concepts = str(parsed_json[response_keys[2]])
        cleaned_response["concepts"] = clean_concepts_text(raw_concepts)

    # 필수 필드 검증 - 하나라도 없으면 에러로 처리
    missing_fields = [field for field in response_keys if field not in cleaned_response]

    if missing_fields:
        logger.info(f"필수 필드 누락: {missing_fields}")
        # 원본 JSON을 문자열로 변환하여 에러 메시지로 전달
        raise Exception(str(parsed_json))

    return cleaned_response

def clean_latex_in_text(text: str) -> str:
    """텍스트에서 LaTeX 수식을 읽기 쉬운 형태로 변환합니다 (범용 처리)."""

    # 1. LaTeX 수식 구분자 제거
    # 인라인 수식: \( ... \) 또는 $ ... $
    text = re.sub(r'\\?\\\(', '', text)  # \( 제거
    text = re.sub(r'\\?\\\)', '', text)  # \) 제거
    text = re.sub(r'(?<!\\)\$', '', text)  # $ 제거 (앞에 \가 없는 경우만)

    # 디스플레이 수식: \[ ... \] 또는 $$ ... $$
    text = re.sub(r'\\?\\\[', '', text)  # \[ 제거
    text = re.sub(r'\\?\\\]', '', text)  # \] 제거
    text = re.sub(r'\$\$', '', text)  # $$ 제거

    # 2. 주요 구조적 명령어 변환
    # 분수: \frac{a}{b} → (a/b)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1/\2)', text)

    # 제곱근: \sqrt{x} → √(x)
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', text)

    # 3. 범용 백슬래시 명령어 제거 (모든 \command 형태)
    # \alpha, \sin, \tan, \log 등 모든 LaTeX 명령어를 공백으로 대체
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)

    # 4. 중괄호 제거 (내용만 남기기)
    text = re.sub(r'[{}]', '', text)

    # 5. 위첨자/아래첨자 기호만 남기기
    # ^ 와 _ 는 유지 (수식에서 의미 전달)

    # 6. 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def clean_answer_text(text: str) -> str:
    """정답 텍스트를 정리합니다."""

    # LaTeX 수식 범용 처리
    text = clean_latex_in_text(text)

    # 불필요한 문자 제거
    # 시작과 끝의 따옴표 제거
    text = re.sub(r'^["\']+|["\']+$', '', text.strip())
    # 끝의 쉼표나 마침표 제거
    text = re.sub(r'[,\.]+$', '', text.strip())
    # 불필요한 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def clean_solution_text(text: str) -> str:
    """풀이과정 텍스트를 정리합니다."""

    # 불필요한 문자 제거
    text = text.strip()

    # LaTeX 수식 범용 처리
    text = clean_latex_in_text(text)

    # JSON 코드블록이 포함된 경우 제거
    text = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # 과도한 반복 제거 (같은 문장이 3번 이상 반복되는 경우)
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if line and line not in filtered_lines[-2:]:  # 최근 2줄과 다른 경우만 추가
            filtered_lines.append(line)

    text = '\n'.join(filtered_lines)

    # 길이 제한 (1000자)
    if len(text) > 1000:
        # 문장 단위로 자르기
        sentences = re.split(r'[.!?]\s+', text)
        result = ""
        for sentence in sentences:
            if len(result + sentence) < 1000:
                result += sentence + ". "
            else:
                break
        text = result.strip()

    # 불필요한 공백 정리
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def clean_concepts_text(text: str) -> str:
    """핵심개념 텍스트를 정리합니다."""

    # 불필요한 문자 제거
    text = text.strip()

    # LaTeX 수식 범용 처리
    text = clean_latex_in_text(text)

    # 길이 제한 (300자)
    if len(text) > 300:
        text = text[:300].rsplit('.', 1)[0] + "."

    # 불필요한 공백 정리
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
