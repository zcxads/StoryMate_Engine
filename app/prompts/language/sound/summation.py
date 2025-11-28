"""
요약 관련 프롬프트 템플릿
"""

TEXT_SUMMARIZATION_TEMPLATE = """다음 책 내용을 배경음악 선택을 위해 매우 간결하게 요약해주세요.

요약 시 다음 사항을 반드시 지켜주세요:
1. 책의 주요 분위기와 톤을 3-4개의 핵심 단어로 표현하세요.
2. 책에서 전달하는 감정과 주요 테마를 짧게 기술하세요.
3. 절대 150단어를 넘지 마세요. 매우 간결해야 합니다.

책 내용: 
{text}

주요 분위기와 감정 요약: """

TEXT_SUMMARIZATION_INPUT_VARIABLES = ["text"]

def get_text_summarization_prompt_config():
    """텍스트 요약 프롬프트 설정을 반환합니다."""
    return {
        "template": TEXT_SUMMARIZATION_TEMPLATE,
        "input_variables": TEXT_SUMMARIZATION_INPUT_VARIABLES
    }
