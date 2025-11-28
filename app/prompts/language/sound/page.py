"""
페이지 관련 프롬프트 템플릿
"""

BACKGROUND_MUSIC_SELECTION_TEMPLATE = """당신은 동화책을 위한 배경음악 전문가입니다. 아래의 장면에 가장 적절한 배경음악을 선택해야 합니다.

장면 내용:
{text}

선택 가능한 배경음악 목록:
{musics}

위 배경음악 중에서 가장 적합한 것을 하나 선택하고, 그 이유를 설명해주세요.
각 배경음악의 유사도 점수는 참고 사항일 뿐이며, 실제 장면의 분위기와 의미에 맞는 가장 적절한 배경음악을 선택해주세요.

응답 형식:
선택: (선택한 배경음악의 번호)
이유: (선택한 이유 상세 설명)"""

BACKGROUND_MUSIC_SELECTION_INPUT_VARIABLES = ["text", "musics"]


def get_background_music_selection_prompt_config():
    """배경음악 선택 프롬프트 설정을 반환합니다."""
    return {
        "template": BACKGROUND_MUSIC_SELECTION_TEMPLATE,
        "input_variables": BACKGROUND_MUSIC_SELECTION_INPUT_VARIABLES
    }
