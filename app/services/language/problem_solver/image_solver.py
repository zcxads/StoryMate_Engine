"""
Problem Solver 전용 이미지 기반 문제 해결 서비스
explanation 모듈에서 독립적으로 분리
"""

import base64
import re
import os
import json
from typing import Dict, Any

from app.prompts.language.problem_solver.solver import create_problem_solving_prompt
from app.utils.logger.setup import setup_logger
from app.core.config import settings
from app.utils.language.generator import call_llm

# 로거 설정
logger = setup_logger('problem_solver_image', 'logs/services')

async def solve_problem_from_image(image_base64: str, model: str = None, language: str = "ko", additional_images: list = None) -> Dict[str, Any]:
    """
    Base64로 인코딩된 이미지에서 문제를 분석하고 해결합니다.

    Args:
        image_base64: Base64로 인코딩된 주요 이미지 데이터
        model: 사용할 언어 모델 (기본값: settings.llm_advanced_analysis_model)
        language: 응답 언어 (기본값: ko - 한국어)
        additional_images: 추가 이미지들의 Base64 데이터 리스트 (옵션)

    Returns:
        Dict[str, Any]: 구조화된 응답 데이터
    """
    # 모델이 지정되지 않은 경우 중앙 설정 사용
    if not model:
        model = settings.llm_advanced_analysis_model

    logger.info(f"Problem Solver 문제 해결 시작 - 모델: {model}, 언어: {language}")

    try:
        # 프롬프트 생성
        prompt_text = create_problem_solving_prompt(language)

        logger.info(f"모델 준비 완료")

        # Base64 이미지 데이터 처리
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]

        # 다중 이미지 지원을 위한 로그
        total_images = 1 + (len(additional_images) if additional_images else 0)
        logger.info(f"처리할 이미지 수: {total_images}")

        # 메시지 컨텐츠 구성
        message_content = [{"type": "text", "text": prompt_text}]

        # 주요 이미지 추가
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

        # 추가 이미지들 추가
        if additional_images:
            for i, additional_image in enumerate(additional_images):
                # Base64 데이터 처리
                if additional_image.startswith('data:image'):
                    additional_image = additional_image.split(',')[1]

                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{additional_image}"
                    }
                })
                logger.info(f"추가 이미지 {i+1} 포함됨")

        # 이미지와 텍스트를 포함한 메시지 생성
        messages = [
            {
                "role": "user",
                "content": message_content
            }
        ]

        logger.info("LLM 호출 시작...")

        # LLM 호출 - call_llm 사용
        response = await call_llm(prompt=messages, model=model)
        result_text = response.content

        logger.info("Problem Solver 문제 해결 완료")
        logger.info(f"LLM 응답 길이: {len(result_text)} 문자")

        # JSON 응답 파싱 및 정리
        parsed_response = parse_and_clean_response(result_text, language)

        return parsed_response

    except Exception as e:
        logger.error(f"Problem Solver 문제 해결 중 오류 발생: {str(e)}", exc_info=True)
        return get_error_response(language, str(e))

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

        # JSON 코드 블록 제거 (```json ... ```)
        json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 직접 JSON 형태 추출 시도
            json_match = re.search(r'(\{.*\})', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = cleaned_text

        # JSON 파싱
        parsed_json = json.loads(json_str)

        # 응답 정리
        cleaned_response = clean_json_response(parsed_json, language)

        logger.info(f"JSON 파싱 및 정리 완료 - 언어: {language}")
        return cleaned_response

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {str(e)}")
        # JSON 파싱 실패 시 텍스트 파싱으로 대체
        return fallback_text_parsing(response_text, language)
    except Exception as e:
        logger.error(f"응답 파싱 중 오류: {str(e)}")
        return get_error_response(language, str(e))

def clean_json_response(parsed_json: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    파싱된 JSON 응답을 정리합니다.
    """
    # 기본 메시지 언어별 설정
    default_messages = {
        "ko": {
            "answer": "답을 찾을 수 없습니다.",
            "solution": "풀이 과정을 생성할 수 없습니다.",
            "concepts": "핵심 개념을 추출할 수 없습니다."
        },
        "en": {
            "answer": "Unable to find the answer.",
            "solution": "Unable to generate solution process.",
            "concepts": "Unable to extract key concepts."
        }
    }

    defaults = default_messages.get(language, default_messages["ko"])

    # 각 필드별로 정리
    cleaned_response = {}

    # 정답 정리
    answer_keys = ["answer", "정답", "답안"]
    answer_found = False
    for key in answer_keys:
        if key in parsed_json:
            raw_answer = str(parsed_json[key])
            cleaned_response["answer"] = clean_text(raw_answer)
            answer_found = True
            break
    if not answer_found:
        cleaned_response["answer"] = defaults["answer"]

    # 풀이과정 정리
    solution_keys = ["solution", "solution_process", "풀이과정"]
    solution_found = False
    for key in solution_keys:
        if key in parsed_json:
            raw_solution = str(parsed_json[key])
            cleaned_response["solution"] = clean_text(raw_solution)
            solution_found = True
            break
    if not solution_found:
        cleaned_response["solution"] = defaults["solution"]

    # 핵심개념 정리
    concepts_keys = ["concepts", "key_concepts", "핵심개념"]
    concepts_found = False
    for key in concepts_keys:
        if key in parsed_json:
            raw_concepts = str(parsed_json[key])
            cleaned_response["concepts"] = clean_text(raw_concepts)
            concepts_found = True
            break
    if not concepts_found:
        cleaned_response["concepts"] = defaults["concepts"]

    return cleaned_response

def clean_text(text: str) -> str:
    """텍스트를 정리합니다."""
    if not text:
        return ""

    # 불필요한 문자 제거
    text = re.sub(r'^["\']+|["\']+$', '', text.strip())
    text = re.sub(r'[,\.]+$', '', text.strip())
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def fallback_text_parsing(response_text: str, language: str) -> Dict[str, Any]:
    """
    JSON 파싱 실패 시 텍스트 파싱으로 대체합니다.
    """
    logger.info("JSON 파싱 실패, 텍스트 파싱으로 대체")

    # 기본 메시지
    default_messages = {
        "ko": {
            "answer": "정답을 추출할 수 없습니다.",
            "concepts": "핵심 개념을 추출할 수 없습니다."
        },
        "en": {
            "answer": "Unable to extract the answer.",
            "concepts": "Unable to extract key concepts."
        }
    }

    defaults = default_messages.get(language, default_messages["ko"])

    # 기본 응답 구조
    result = {
        "answer": defaults["answer"],
        "solution": clean_text(response_text),
        "concepts": defaults["concepts"]
    }

    # 간단한 텍스트 파싱 시도
    try:
        # 정답 추출 시도
        answer_patterns = [
            r'답.*?[:：]\s*([^\n]+)',
            r'Answer.*?[:：]\s*([^\n]+)',
            r'정답.*?[:：]\s*([^\n]+)',
            r'(\d+)'
        ]

        for pattern in answer_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                raw_answer = match.group(1).strip()
                result["answer"] = clean_text(raw_answer)
                break

    except Exception as e:
        logger.error(f"텍스트 파싱 중 오류: {str(e)}")

    return result

def get_error_response(language: str, error_message: str) -> Dict[str, Any]:
    """
    오류 발생 시 언어별 기본 응답을 반환합니다.
    """
    error_messages = {
        "ko": {
            "answer": "문제를 해결할 수 없습니다.",
            "solution": f"처리 중 오류가 발생했습니다: {error_message}",
            "concepts": "핵심 개념을 추출할 수 없습니다."
        },
        "en": {
            "answer": "Unable to solve the problem.",
            "solution": f"An error occurred during processing: {error_message}",
            "concepts": "Unable to extract key concepts."
        }
    }

    messages = error_messages.get(language, error_messages["ko"])

    return {
        "answer": messages["answer"],
        "solution": messages["solution"],
        "concepts": messages["concepts"]
    }