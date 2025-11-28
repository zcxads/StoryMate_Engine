"""
사운드 효과 관련 프롬프트 템플릿
"""

SOUND_EFFECT_SELECTION_TEMPLATE = """당신은 동화책을 위한 효과음 전문가입니다. 아래의 문장에 가장 적절한 효과음을 선택해야 합니다.

문장: {text}

선택 가능한 효과음 목록:
{effects}

위 효과음 중에서 가장 적합한 것을 하나 선택하고, 그 이유를 설명해주세요. 
각 효과음의 유사도 점수는 참고 사항일 뿐이며, 실제 문맥과 의미에 맞는 가장 적절한 효과음을 선택해주세요.

응답 형식:
선택: (선택한 효과음의 번호)
이유: (선택한 이유 상세 설명)"""

SOUND_EFFECT_POSITION_TEMPLATE = """당신은 전문 효과음 타이밍 감독입니다. 각 효과음의 재생 시점과 지속 시간을 결정해야 합니다.

주의사항:
1. 이야기의 자연스러운 흐름을 고려하세요
2. 의도적인 경우가 아니라면 효과음이 겹치지 않도록 하세요
3. 예상 읽기 속도에 맞춰 타이밍을 조절하세요

{format_instructions}

다음은 현재 페이지의 내용과 선택된 효과음입니다:
{page_content}
{effects_content}

각 효과음의 적절한 재생 시점과 지속 시간을 결정해주세요.
- 각 페이지는 기본적으로 15초 동안 보여집니다
- 문장 당 평균 3초의 읽기 시간을 고려하세요
- 각 문장에 0부터 10사이의 값으로 위치를 지정하세요
- 효과음은 해당 문장이 읽히기 시작할 때 재생되어야 합니다"""

SOUND_EFFECT_SELECTION_INPUT_VARIABLES = ["text", "effects"]
SOUND_EFFECT_POSITION_INPUT_VARIABLES = ["page_content", "effects_content"]

def get_sound_effect_selection_prompt_config():
    """효과음 선택 프롬프트 설정을 반환합니다."""
    return {
        "template": SOUND_EFFECT_SELECTION_TEMPLATE,
        "input_variables": SOUND_EFFECT_SELECTION_INPUT_VARIABLES
    }

def get_sound_effect_position_prompt_config():
    """효과음 위치 설정 프롬프트 설정을 반환합니다."""
    return {
        "template": SOUND_EFFECT_POSITION_TEMPLATE,
        "input_variables": SOUND_EFFECT_POSITION_INPUT_VARIABLES
    }
