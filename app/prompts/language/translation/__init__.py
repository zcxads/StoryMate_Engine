"""
Translation prompts - Language-specific modules
"""

# Import language-specific templates
from .ko import KOREAN_TRANSLATION_TEMPLATE
from .en import ENGLISH_TRANSLATION_TEMPLATE
from .ja import JAPANESE_TRANSLATION_TEMPLATE
from .zh import CHINESE_TRANSLATION_TEMPLATE
from .es import SPANISH_TRANSLATION_TEMPLATE
from .fr import FRENCH_TRANSLATION_TEMPLATE
from .de import GERMAN_TRANSLATION_TEMPLATE
from .it import ITALIAN_TRANSLATION_TEMPLATE
from .pt import PORTUGUESE_TRANSLATION_TEMPLATE
from .ru import RUSSIAN_TRANSLATION_TEMPLATE
from .nl import DUTCH_TRANSLATION_TEMPLATE
from .pl import POLISH_TRANSLATION_TEMPLATE
from .sv import SWEDISH_TRANSLATION_TEMPLATE
from .no import NORWEGIAN_TRANSLATION_TEMPLATE
from .da import DANISH_TRANSLATION_TEMPLATE
from .fi import FINNISH_TRANSLATION_TEMPLATE
from .cs import CZECH_TRANSLATION_TEMPLATE
from .hu import HUNGARIAN_TRANSLATION_TEMPLATE
from .ro import ROMANIAN_TRANSLATION_TEMPLATE
from .el import GREEK_TRANSLATION_TEMPLATE
from .uk import UKRAINIAN_TRANSLATION_TEMPLATE
from .sr import SERBIAN_TRANSLATION_TEMPLATE
from .sk import SLOVAK_TRANSLATION_TEMPLATE
from .sl import SLOVENIAN_TRANSLATION_TEMPLATE
from .hr import CROATIAN_TRANSLATION_TEMPLATE
from .bg import BULGARIAN_TRANSLATION_TEMPLATE
from .ca import CATALAN_TRANSLATION_TEMPLATE
from .ar import ARABIC_TRANSLATION_TEMPLATE
from .he import HEBREW_TRANSLATION_TEMPLATE
from .fa import PERSIAN_TRANSLATION_TEMPLATE
from .tr import TURKISH_TRANSLATION_TEMPLATE
from .hi import HINDI_TRANSLATION_TEMPLATE
from .vi import VIETNAMESE_TRANSLATION_TEMPLATE
from .th import THAI_TRANSLATION_TEMPLATE
from .id import INDONESIAN_TRANSLATION_TEMPLATE
from .ms import MALAY_TRANSLATION_TEMPLATE
from .be import BELARUSIAN_TRANSLATION_TEMPLATE
from .hy import ARMENIAN_TRANSLATION_TEMPLATE
from .az import AZERBAIJANI_TRANSLATION_TEMPLATE

# Language names mapping
LANGUAGE_NAMES = {
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "el": "Greek",
    "uk": "Ukrainian",
    "sr": "Serbian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "hr": "Croatian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "ar": "Arabic",
    "he": "Hebrew",
    "fa": "Persian",
    "tr": "Turkish",
    "hi": "Hindi",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "be": "Belarusian",
    "hy": "Armenian",
    "az": "Azerbaijani"
}

TRANSLATION_INPUT_VARIABLES = ["text"]

def get_translation_template(target_language: str) -> str:
    """Get translation template for target language"""
    templates = {
        "ko": KOREAN_TRANSLATION_TEMPLATE,
        "en": ENGLISH_TRANSLATION_TEMPLATE,
        "ja": JAPANESE_TRANSLATION_TEMPLATE,
        "zh": CHINESE_TRANSLATION_TEMPLATE,
        "es": SPANISH_TRANSLATION_TEMPLATE,
        "fr": FRENCH_TRANSLATION_TEMPLATE,
        "de": GERMAN_TRANSLATION_TEMPLATE,
        "it": ITALIAN_TRANSLATION_TEMPLATE,
        "pt": PORTUGUESE_TRANSLATION_TEMPLATE,
        "ru": RUSSIAN_TRANSLATION_TEMPLATE,
        "nl": DUTCH_TRANSLATION_TEMPLATE,
        "pl": POLISH_TRANSLATION_TEMPLATE,
        "sv": SWEDISH_TRANSLATION_TEMPLATE,
        "no": NORWEGIAN_TRANSLATION_TEMPLATE,
        "da": DANISH_TRANSLATION_TEMPLATE,
        "fi": FINNISH_TRANSLATION_TEMPLATE,
        "cs": CZECH_TRANSLATION_TEMPLATE,
        "hu": HUNGARIAN_TRANSLATION_TEMPLATE,
        "ro": ROMANIAN_TRANSLATION_TEMPLATE,
        "el": GREEK_TRANSLATION_TEMPLATE,
        "uk": UKRAINIAN_TRANSLATION_TEMPLATE,
        "sr": SERBIAN_TRANSLATION_TEMPLATE,
        "sk": SLOVAK_TRANSLATION_TEMPLATE,
        "sl": SLOVENIAN_TRANSLATION_TEMPLATE,
        "hr": CROATIAN_TRANSLATION_TEMPLATE,
        "bg": BULGARIAN_TRANSLATION_TEMPLATE,
        "ca": CATALAN_TRANSLATION_TEMPLATE,
        "ar": ARABIC_TRANSLATION_TEMPLATE,
        "he": HEBREW_TRANSLATION_TEMPLATE,
        "fa": PERSIAN_TRANSLATION_TEMPLATE,
        "tr": TURKISH_TRANSLATION_TEMPLATE,
        "hi": HINDI_TRANSLATION_TEMPLATE,
        "vi": VIETNAMESE_TRANSLATION_TEMPLATE,
        "th": THAI_TRANSLATION_TEMPLATE,
        "id": INDONESIAN_TRANSLATION_TEMPLATE,
        "ms": MALAY_TRANSLATION_TEMPLATE,
        "be": BELARUSIAN_TRANSLATION_TEMPLATE,
        "hy": ARMENIAN_TRANSLATION_TEMPLATE,
        "az": AZERBAIJANI_TRANSLATION_TEMPLATE,
    }
    
    return templates.get(target_language, ENGLISH_TRANSLATION_TEMPLATE)


def get_translation_prompt_config(target_language: str):
    """Get translation prompt configuration"""
    return {
        "template": get_translation_template(target_language),
        "input_variables": TRANSLATION_INPUT_VARIABLES
    }


def get_language_names():
    """Get supported language names mapping"""
    return LANGUAGE_NAMES


def get_json_array_translation_prompt(target_language: str, total_texts: int, input_json: str) -> str:
    """
    JSON 배열 방식 번역 프롬프트 생성

    Args:
        target_language: 목표 언어 코드
        total_texts: 번역할 텍스트 개수
        input_json: 입력 JSON 배열 문자열

    Returns:
        완성된 번역 프롬프트
    """
    language_template = get_translation_template(target_language)
    language_name = LANGUAGE_NAMES.get(target_language, target_language.upper())

    prompt = f"""You will receive a JSON array with {total_texts} text items.
Translate each item into {language_name} and return a JSON array with EXACTLY {total_texts} translated items.

INPUT FORMAT: ["text1", "text2", ..., "text{total_texts}"]
OUTPUT FORMAT: ["translated1", "translated2", ..., "translated{total_texts}"]

CRITICAL RULES:
1. Output MUST be a valid JSON array
2. Output MUST have EXACTLY {total_texts} items (same as input)
3. Maintain the exact same order as input
4. Each item corresponds to the same index in input
5. Do NOT add any explanation, only output the JSON array

{language_template}

Input JSON array:
{input_json}

Output (JSON array only):"""

    return prompt


__all__ = [
    "get_translation_template",
    "get_translation_prompt_config",
    "get_language_names",
    "get_json_array_translation_prompt",
    "LANGUAGE_NAMES",
    "TRANSLATION_INPUT_VARIABLES",
]
