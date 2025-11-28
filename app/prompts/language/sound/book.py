BOOK_BACKGROUND_MUSIC_SELECTION_TEMPLATE = """당신은 동화책을 위한 배경음악 전문가입니다. 아래의 책 내용을 전체적으로 분석하여 가장 적절한 배경음악을 선택해야 합니다.

책 내용:
{text}

선택 가능한 배경음악 목록:
{musics}

위 배경음악 중에서 가장 적합한 것을 하나 선택하고, 그 이유를 설명해주세요.
책의 전반적인 분위기, 주제, 감정을 반영하는 배경음악을 선택하세요.

반드시 아래 형식을 정확히 따라 응답해주세요:
선택: [1-5 사이의 숫자만 입력]
이유: [선택 이유 설명]

예시 응답:
선택: 3
이유: 이 음악은 책의 동화적 분위기와 잘 어울리며..."""

BOOK_BACKGROUND_MUSIC_SELECTION_INPUT_VARIABLES = ["text", "musics"]

def get_book_background_music_selection_prompt_config():
    """책 전체 배경음악 선택 프롬프트 설정을 반환합니다."""
    return {
        "template": BOOK_BACKGROUND_MUSIC_SELECTION_TEMPLATE,
        "input_variables": BOOK_BACKGROUND_MUSIC_SELECTION_INPUT_VARIABLES
    }
