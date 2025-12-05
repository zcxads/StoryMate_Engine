import re
from typing import Dict, Any

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.models.state import PlayOutput
from app.utils.logger.setup import setup_logger
from app.prompts.language.play.generator import get_play_prompt_config
from app.utils.language.generator import language_generator

# 로거 설정
logger = setup_logger('play_generator', 'logs/play')

# 금지된 speaker 이름 목록
FORBIDDEN_ROLES = {
    "family", "everyone", "all", "group", "chorus",
    "가족", "모두", "전체", "children", "people", "crowd",
    "together", "함께", "全員", "みんな", "전원", "다함께"
}

def validate_script_roles(script: str) -> tuple[bool, list[str]]:
    """
    스크립트에서 금지된 role 이름이 사용되었는지 검증

    Returns:
        tuple[bool, list[str]]: (유효 여부, 발견된 금지 role 목록)
    """
    forbidden_found = []

    # 스크립트의 각 라인 검사
    for line in script.split('\n'):
        line = line.strip()

        # role: text 패턴 매칭
        match = re.match(r'^([a-zA-Z가-힣0-9]+):\s*(.+)$', line)
        if match:
            role = match.group(1).strip().lower()

            # 금지된 role 체크
            if role in FORBIDDEN_ROLES:
                forbidden_found.append(role)
                logger.warning(f"🚫 금지된 role 발견: '{role}' in line: '{line[:60]}...'")

    is_valid = len(forbidden_found) == 0
    return is_valid, forbidden_found

@traceable(run_type="chain")
async def play_generator(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """연극 대사 생성 에이전트 (금지된 role 검증 및 재생성 로직 포함)"""
    try:
        logger.info("Starting play generation process")
        state = state.get("state", state)

        # 모든 페이지의 텍스트 결합 (딕셔너리 접근)
        combined_text = " ".join([
            text["text"]
            for page in state["pages"]
            for text in page["texts"]
        ])

        # 언어 감지
        detected_language = "ko"  # 기본값
        if combined_text.strip():
            try:
                from app.services.language.language_detection.detector import detect_language_with_ai
                detection_result = await detect_language_with_ai(combined_text.strip())

                detected_lang_code = detection_result.get("primary_language")
                confidence = detection_result.get("confidence", 0.0)
                logger.info(f"언어 감지 결과: {detected_lang_code} - 신뢰도: {confidence:.3f}")
                detected_language = detected_lang_code
                
            except Exception as e:
                logger.warning(f"AI 언어 감지 실패, 기본값(en) 사용: {e}")

        # state에 명시된 언어가 있으면 우선 사용, 없으면 감지된 언어 사용
        language = state.get("language", detected_language)
        logger.info(f"사용할 언어: {language}")

        # 출력 파서 설정 (간단 스키마: playTitle, script)
        parser = JsonOutputParser(pydantic_object=PlayOutput)
        format_instructions = parser.get_format_instructions()

        # 프롬프트 설정 가져오기 (언어 기반 분기)
        prompt_config = get_play_prompt_config(language)

        # 프롬프트 템플릿 생성
        prompt = PromptTemplate(
            template=prompt_config["template"],
            input_variables=prompt_config["input_variables"],
            partial_variables={"format_instructions": format_instructions}
        )

        # 체인 생성 및 실행
        chain = prompt | language_generator

        logger.info(f"Generating play in {language}")

        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", "gemini")

        # 재시도 로직: 최대 3번 시도
        max_retries = 3
        parsed_result = None

        for attempt in range(1, max_retries + 1):
            logger.info(f"🎭 Play generation attempt {attempt}/{max_retries}")

            result = await chain.ainvoke({
                "text": combined_text
            }, config={"model": model_name})

            # JSON 결과 파싱
            try:
                parsed_result = parser.parse(result.content)
            except Exception as parse_error:
                logger.error(f"JSON parsing error: {parse_error}")
                logger.error(f"Raw result: {result.content[:500]}...")
                if attempt == max_retries:
                    raise
                else:
                    logger.info(f"Retrying due to parsing error...")
                    continue

            # 스크립트 검증: 금지된 role 이름 체크
            script = parsed_result.get("script", "")
            is_valid, forbidden_roles = validate_script_roles(script)

            if is_valid:
                logger.info(f"✅ 스크립트 검증 성공 (attempt {attempt}) - 금지된 role 없음")
                break
            else:
                logger.warning(f"❌ 스크립트 검증 실패 (attempt {attempt}) - 금지된 role 발견: {forbidden_roles}")
                if attempt < max_retries:
                    logger.info(f"🔄 재생성 시도 중... (금지된 role: {', '.join(forbidden_roles)})")
                else:
                    logger.error(f"❌ {max_retries}번 시도했지만 금지된 role이 계속 생성됨: {forbidden_roles}")
                    logger.error(f"생성된 스크립트:\n{script[:500]}...")
                    # 최종 실패: 에러를 던지지 않고 경고만 로그 (TTS 생성 단계에서 필터링됨)
                    logger.warning("⚠️ 금지된 role이 포함된 스크립트를 반환합니다. TTS 생성 시 해당 라인은 건너뛰게 됩니다.")

        # 결과를 dict로 처리
        logger.info(f"Generated play with title: {parsed_result['playTitle']}")

        # state 업데이트 (간단 스키마를 그대로 저장)
        state["raw_play"] = {
            "playTitle": parsed_result["playTitle"],
            "script": parsed_result["script"]
        }

        logger.info("Play generation completed successfully")
        return {"state": state}

    except Exception as e:
        logger.error(f"Error in play generator: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return {"state": state}
