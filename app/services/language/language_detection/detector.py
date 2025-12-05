import json
import logging
import re
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from langsmith.run_helpers import traceable
from langchain_core.prompts import PromptTemplate

from app.utils.logger.setup import setup_logger
from app.utils.language.generator import language_generator
from app.prompts.language.language_detection.detector import get_language_detection_prompt_config, get_supported_languages
from app.core.config import settings

# 로거 설정
logger = setup_logger('language_detection', 'logs/language')

@traceable(run_type="chain")
async def detect_language_with_ai(text: str, model_name: str = None) -> Dict[str, any]:
    """
    AI 모델을 사용하여 텍스트의 언어를 감지합니다.

    Args:
        text: 언어를 감지할 텍스트
        model_name: 사용할 AI 모델 (기본값: 중앙 설정에서 가져옴)

    Returns:
        Dict containing:
        - primary_language: 주요 언어 코드
        - confidence: 신뢰도 (0.0-1.0)
        - detected_languages: 감지된 모든 언어 목록
        - is_mixed: 혼합 언어 여부
    """
    try:
        # 모델이 지정되지 않은 경우 중앙 설정 사용
        if not model_name:
            model_name = settings.default_llm_model

        logger.info(f"Starting AI language detection for text: '{text[:50]}...' using {model_name}")

        # 텍스트가 비어있거나 너무 짧은 경우
        if not text or len(text.strip()) <= 1:
            logger.warning("Text is empty or too short for language detection")
            return {
                "primary_language": "unknown",
                "confidence": 0.0,
                "detected_languages": [],
                "is_mixed": False,
                "error": "Text too short"
            }

        # 텍스트 샘플링 (500자 초과 시 20%만 사용)
        original_length = len(text)
        if original_length > 500:
            sample_size = int(original_length * 0.2)
            # 앞쪽 10% + 중간 10% 추출
            first_half_size = sample_size // 2
            second_half_size = sample_size - first_half_size

            front_sample = text[:first_half_size]
            middle_start = (original_length - second_half_size) // 2
            middle_sample = text[middle_start:middle_start + second_half_size]

            sampled_text = front_sample + " ... " + middle_sample
            logger.info(f"Text sampling 결과: {sampled_text}")
            text = sampled_text

        # 프롬프트 생성
        prompt_config = get_language_detection_prompt_config()
        prompt = PromptTemplate(
            template=prompt_config["template"]
        )

        # AI 모델 호출
        chain = prompt | language_generator
        response = await chain.ainvoke(
            {"text": text},
            config={"model": model_name}
        )
        
        # 응답 파싱
        result = parse_language_detection_response(response.content.strip())
        
        logger.info(f"AI Language detection completed: {result['primary_language']} (confidence: {result['confidence']})")
        return result
        
    except Exception as e:
        logger.error(f"Error in AI language detection: {str(e)}", exc_info=True)
        return result

def parse_language_detection_response(response: str) -> Dict[str, any]:
    """
    AI 모델의 응답을 파싱하여 구조화된 결과로 변환
    
    Expected response format:
    PRIMARY: ko
    CONFIDENCE: 0.95
    DETECTED: ko, en
    MIXED: false
    """
    try:
        lines = response.strip().split('\n')
        result = {
            "primary_language": "unknown",
            "confidence": 0.0,
            "detected_languages": [],
            "is_mixed": False
        }
        
        supported_languages = get_supported_languages()
        
        for line in lines:
            line = line.strip()
            if line.startswith("PRIMARY:"):
                result["primary_language"] = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":", 1)[1].strip())
                except ValueError:
                    result["confidence"] = 0.0
            elif line.startswith("DETECTED:"):
                languages_str = line.split(":", 1)[1].strip()
                result["detected_languages"] = [lang.strip() for lang in languages_str.split(",") if lang.strip()]
            elif line.startswith("MIXED:"):
                mixed_str = line.split(":", 1)[1].strip().lower()
                result["is_mixed"] = mixed_str in ["true", "yes", "1"]
        
        # 검증
        if result["primary_language"] not in supported_languages and result["primary_language"] != "unknown":
            logger.warning(f"Unknown primary language detected: {result['primary_language']}")
            result["primary_language"] = "unknown"
        
        # detected_languages가 비어있으면 primary_language로 채움
        if not result["detected_languages"] and result["primary_language"] != "unknown":
            result["detected_languages"] = [result["primary_language"]]
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing AI response: {str(e)}")
        return {
            "primary_language": "unknown",
            "confidence": 0.0,
            "detected_languages": [],
            "is_mixed": False,
            "error": f"Parsing failed: {str(e)}"
        }

async def is_translation_needed_ai(text: str, target_language: str, model_name: str = None) -> bool:
    """
    AI 기반 언어 감지를 사용하여 번역이 필요한지 판단

    Args:
        text: 분석할 텍스트
        target_language: 대상 언어
        model_name: 사용할 AI 모델 (기본값: 중앙 설정에서 가져옴)

    Returns:
        bool: 번역이 필요하면 True, 아니면 False
    """
    try:
        # 모델이 지정되지 않은 경우 중앙 설정 사용
        if not model_name:
            model_name = settings.default_llm_model

        # AI 언어 감지 수행
        detection_result = await detect_language_with_ai(text, model_name)
        
        if detection_result.get("error"):
            logger.warning(f"AI detection failed: {detection_result.get('error')}")
        
        primary_language = detection_result["primary_language"]
        confidence = detection_result["confidence"]
        detected_languages = detection_result["detected_languages"]
        is_mixed = detection_result["is_mixed"]
        
        logger.info(f"🔍 AI Detection: primary={primary_language}, confidence={confidence:.2f}, detected={detected_languages}, mixed={is_mixed}")
        
        # 감지 실패한 경우
        if primary_language == "unknown":
            logger.info("🔍 AI Detection: Low confidence or unknown language -> default to translation needed")
            return True
        
        # 이미 대상 언어인 경우
        if primary_language == target_language:
            if confidence >= 0.8:
                logger.info(f"🔍 AI Detection: High confidence match with target language -> no translation needed")
                return False
            else:
                logger.info(f"🔍 AI Detection: Low confidence match -> translation recommended")
                return True
        
        # 다른 언어인 경우
        logger.info(f"🔍 AI Detection: Different language detected ({primary_language} -> {target_language}) -> translation needed")
        return True
        
    except Exception as e:
        logger.error(f"Error in AI-based translation decision: {str(e)}", exc_info=True)
        # 오류 시 안전하게 번역 필요로 판단
        return True
