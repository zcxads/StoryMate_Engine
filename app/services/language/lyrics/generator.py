import logging
from typing import Dict, Any

from langsmith.run_helpers import traceable

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.models.state import LyricsOutput
from app.utils.logger.setup import setup_logger
from app.prompts.language.lyrics.generator import get_lyrics_prompt_config
from app.utils.language.generator import language_generator

# 로거 설정
logger = setup_logger('lyrics_generator', 'logs/lyrics')

@traceable(run_type="chain")
async def lyrics_generator(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """노래 가사 생성 에이전트"""
    try:
        logger.info("Starting lyrics generation process")
        state = state.get("state", state)
        
        # 모든 페이지의 텍스트 결합 (딕셔너리 접근)
        combined_text = " ".join([
            text["text"]
            for page in state["pages"]
            for text in page["texts"]
        ])

        # AI 기반 언어 감지
        detected_language = "ko"  # 기본값
        if combined_text.strip():
            try:
                from app.services.language.language_detection.detector import detect_language_with_ai
                detection_result = await detect_language_with_ai(combined_text.strip())
                detected_language = detection_result.get("primary_language")
                confidence = detection_result.get("confidence", 0.0)
                logger.info(f"AI 언어 감지 결과: {detected_language} - 신뢰도: {confidence:.3f}")
            except Exception as e:
                logger.warning(f"AI 언어 감지 실패, 기본값(en) 사용: {e}")

        # state에 명시된 언어가 있으면 우선 사용, 없으면 감지된 언어 사용
        language = state.get("language", detected_language)
        logger.info(f"사용할 언어: {language}")

        # 출력 파서 설정
        parser = JsonOutputParser(pydantic_object=LyricsOutput)
        format_instructions = parser.get_format_instructions()

        # 프롬프트 설정 가져오기 (감지된 언어 사용)
        prompt_config = get_lyrics_prompt_config(language=language)
        
        # 프롬프트 템플릿 생성
        prompt = PromptTemplate(
            template=prompt_config["template"],
            input_variables=prompt_config["input_variables"],
            partial_variables={"format_instructions": format_instructions}
        )

        # 체인 생성 및 실행
        chain = prompt | language_generator
        
        logger.info(f"Generating lyrics in {language}")
        
        # API 요청에서 모델을 받아서 사용
        model_name = kwargs.get("model", "gemini")
        
        result = await chain.ainvoke({
            "text": combined_text,
            "language": state["language"]
        }, config={"model": model_name})
        
        # JSON 결과 파싱
        try:
            parsed_result = parser.parse(result.content)
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {parse_error}")
            logger.error(f"Raw result: {result.content[:500]}...")
            raise
        
        # 결과를 dict로 처리
        logger.info(f"Generated lyrics with title: {parsed_result['songTitle']}")
        
        # state 업데이트 (lyrics는 이미 dict 형태로 가정)
        state["raw_lyrics"] = {
            "songTitle": parsed_result["songTitle"],
            "lyrics": parsed_result["lyrics"]
        }
        
        logger.info("Lyrics generation completed successfully")
        return {"state": state}
        
    except Exception as e:
        logger.error(f"Error in lyrics generator: {str(e)}", exc_info=True)
        state["error"] = str(e)
        return {"state": state}
