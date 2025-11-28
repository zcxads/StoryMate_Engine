import os
import logging
from pydantic import BaseModel
from typing import Any, Dict, Tuple, List

from langsmith.run_helpers import traceable

from langgraph.graph import END

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.models.state import get_valid_sound_state, PageEffectPositions
from app.prompts.language.sound.sentence import get_sound_effect_position_prompt_config
from app.utils.language.generator import language_generator


logger = logging.getLogger(__name__)

class EffectPositionSelections(BaseModel):
    pages: List[PageEffectPositions]

@traceable(run_type="chain")
async def sound_effect_position_agent(state: Dict[str, Any], pageKey: int, model: str = "gemini") -> Tuple[Dict[str, Any], str]:
    try:
        current_state = get_valid_sound_state(state)
        
        parser = JsonOutputParser(pydantic_object=EffectPositionSelections)
        format_instructions = parser.get_format_instructions()
        
        # 프롬프트 설정 가져오기
        prompt_config = get_sound_effect_position_prompt_config()
        template = prompt_config["template"]

        prompt = PromptTemplate(
            template=template,
            input_variables=prompt_config["input_variables"],
            partial_variables={"format_instructions": format_instructions}
        )

        # Get specific page content
        page = next(
            (page for page in current_state.pages if page.pageKey == pageKey),
            None
        )
        
        if page is None:
            raise ValueError(f"No content found for pageKey: {pageKey}")

        page_content = "\n".join([
            f"- {text.text}"
            for text in page.texts
        ])

        # Get effects for this page
        page_effects = next(
            (page_effect for page_effect in current_state.sound_effects if page_effect.pageKey == pageKey),
            None
        )
        
        if page_effects is None:
            raise ValueError(f"No sound effects found for pageKey: {pageKey}")

        effects_content = "\n".join([
            f"Effect: {effect.effectPath} for text: {effect.text}"
            for effect in page_effects.effects
        ])

        chain = prompt | language_generator
        
        result = await chain.ainvoke({
            "page_content": f"[Page {pageKey}]\n{page_content}",
            "effects_content": effects_content
        }, config={"model": model})
        
        # JSON 결과 파싱
        try:
            parsed_result = parser.parse(result.content)
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {parse_error}")
            raise

        # Update state with effect positions for this page
        if not current_state.effect_positions:
            current_state.effect_positions = []
            
        # parsed_result는 딕셔너리이므로 키로 접근
        try:
            page_effect_positions_dict = parsed_result["pages"][0]
            
            # 딕셔너리를 PageEffectPositions 객체로 변환
            page_effect_positions = PageEffectPositions(**page_effect_positions_dict)
            
            # PageEffectPositions 객체 추가
            current_state.effect_positions.append(page_effect_positions)
        except KeyError as e:
            logger.error(f"Key error in parsed_result: {e}")
            logger.error(f"Available keys in parsed_result: {list(parsed_result.keys())}")
            raise
        except Exception as e:
            logger.error(f"Error creating PageEffectPositions: {e}")
            logger.error(f"page_effect_positions_dict: {page_effect_positions_dict}")
            raise
        
        # Check if this is the last page
        all_page_keys = sorted([page.pageKey for page in current_state.pages])
        max_page_key = max(all_page_keys)
        
        # If current page is the last page, end the workflow
        if pageKey == max_page_key:
            return {"state": current_state.model_dump()}, END
        else:
            # Find the next page key
            next_page_idx = all_page_keys.index(pageKey) + 1
            next_page_key = all_page_keys[next_page_idx]
            return {"state": current_state.model_dump()}, f"sound_effect_{next_page_key}"
        
    except Exception as e:
        logger.error(f"Error in sound_effect_position_agent: {str(e)}", exc_info=True)
        raise
