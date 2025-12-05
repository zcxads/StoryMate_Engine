import json
import re
from typing import Dict, Any
from app.utils.logger.setup import setup_logger
from app.utils.language.generator import call_llm
from app.prompts.voice.stt.feature_matcher import get_system_prompt
from app.core.config import settings

logger = setup_logger('feature_matcher')

class FeatureMatcher:
    """기능 매칭 처리기 (OpenAI GPT 기반)"""

    def __init__(self):
        self.model = settings.default_llm_model

    async def match_feature(self, text: str) -> Dict[str, Any]:
        """
        텍스트를 분석하여 앱 기능과 매칭 (모든 응답은 영어로 통일)

        Args:
            text: STT 변환된 텍스트

        Returns:
            Dict: 매칭 결과 (영어)
        """
        try:
            logger.info(f"기능 매칭 시작 - 텍스트: {text}")

            system_prompt = get_system_prompt()

            # call_llm 사용
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ]

            response = await call_llm(prompt=messages, model=self.model)

            # content 추출
            content_str = response.content if hasattr(response, 'content') else str(response)

            # 빈 응답 체크
            if not content_str or content_str.strip() == "":
                logger.error("LLM이 빈 응답을 반환했습니다.")
                return {
                    "matched": False,
                    "component": None,
                    "score": 0.0,
                    "reason": "Empty response from LLM",
                    "message": "An error occurred during feature matching."
                }

            # JSON 코드블록 제거
            if "```json" in content_str:
                content_str = re.search(r'```json\s*(.*?)\s*```', content_str, re.DOTALL)
                if content_str:
                    content_str = content_str.group(1)
                else:
                    logger.error("JSON 코드블록을 찾을 수 없습니다.")
            elif "```" in content_str:
                content_str = re.search(r'```\s*(.*?)\s*```', content_str, re.DOTALL)
                if content_str:
                    content_str = content_str.group(1)

            # JSON 파싱 (trailing commas 제거)
            content_str_cleaned = re.sub(r',\s*([}\]])', r'\1', content_str)
            content_dict = json.loads(content_str_cleaned)

            logger.info(f"기능 매칭 완료 - matched: {content_dict.get('matched')}, component: {content_dict.get('component')}")

            return content_dict

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}", exc_info=True)
            return {
                "matched": False,
                "component": None,
                "score": 0.0,
                "reason": f"Failed to parse response: {str(e)}",
                "message": "An error occurred during feature matching."
            }

        except Exception as e:
            logger.error(f"기능 매칭 중 오류 발생: {str(e)}", exc_info=True)
            return {
                "matched": False,
                "component": None,
                "score": 0.0,
                "reason": f"Error during matching: {str(e)}",
                "message": "An error occurred during feature matching."
            }

async def match_text_to_feature(text: str) -> Dict[str, Any]:
    """
    텍스트를 앱 기능과 매칭하는 함수

    Args:
        text: STT 변환된 텍스트

    Returns:
        Dict: 매칭 결과
    """
    matcher = FeatureMatcher()
    return await matcher.match_feature(text)
