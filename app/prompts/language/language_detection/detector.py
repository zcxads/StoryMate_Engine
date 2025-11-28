"""
Language detection prompt templates for AI-based detection
"""

# 지원하는 언어 목록 (39개 언어)
SUPPORTED_LANGUAGES = {
    # East Asian
    "ko": "Korean",
    "ja": "Japanese",
    "zh": "Chinese",

    # Western European
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ca": "Catalan",

    # Eastern European
    "ru": "Russian",
    "pl": "Polish",
    "uk": "Ukrainian",
    "cs": "Czech",
    "sk": "Slovak",
    "hr": "Croatian",
    "sr": "Serbian",
    "sl": "Slovenian",
    "bg": "Bulgarian",
    "be": "Belarusian",
    "ro": "Romanian",
    "hu": "Hungarian",
    "el": "Greek",

    # Nordic
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",

    # Middle Eastern & South Asian
    "ar": "Arabic",
    "he": "Hebrew",
    "fa": "Persian",
    "tr": "Turkish",
    "az": "Azerbaijani",
    "hy": "Armenian",
    "hi": "Hindi",

    # Southeast Asian
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay"
}

LANGUAGE_DETECTION_TEMPLATE = """You are an expert language detection system. Analyze the given text and determine its language with high precision.

SUPPORTED LANGUAGES (39 languages):
East Asian: ko (Korean), ja (Japanese), zh (Chinese)
Western European: en (English), es (Spanish), fr (French), de (German), it (Italian), pt (Portuguese), nl (Dutch), ca (Catalan)
Eastern European: ru (Russian), pl (Polish), uk (Ukrainian), cs (Czech), sk (Slovak), hr (Croatian), sr (Serbian), sl (Slovenian), bg (Bulgarian), be (Belarusian), ro (Romanian), hu (Hungarian), el (Greek)
Nordic: sv (Swedish), no (Norwegian), da (Danish), fi (Finnish)
Middle Eastern & South Asian: ar (Arabic), he (Hebrew), fa (Persian), tr (Turkish), az (Azerbaijani), hy (Armenian), hi (Hindi)
Southeast Asian: vi (Vietnamese), th (Thai), id (Indonesian), ms (Malay)

CRITICAL ANALYSIS POINTS:
1. SCRIPT-BASED DETECTION (High Priority):
   - Korean: Hangul characters (한글)
   - Japanese: Hiragana (ひらがな) or Katakana (カタカナ)
   - Chinese: Hanzi only (no hiragana/katakana). Simplified uses 们个这那, Traditional uses 們個這那
   - Arabic/Persian: Arabic script (العربية/فارسی)
   - Hebrew: Hebrew script (עברית)
   - Armenian: Armenian script (Հայերեն)
   - Thai: Thai script (ไทย)
   - Hindi: Devanagari script (हिन्दी)
   - Greek: Greek alphabet (Ελληνικά)
   - Cyrillic: Russian, Ukrainian, Serbian, Bulgarian, Belarusian

2. LATIN SCRIPT LANGUAGES (Use common words & patterns):
   - English: the, a, is, are
   - Spanish: el, la, de, que, y
   - French: le, la, de, et, est
   - German: der, die, das, und, ist
   - Turkish: ve, bir, bu, için (uses ç, ğ, ı, ö, ş, ü)
   - Azerbaijani: və, bir, bu, üçün (uses ə, ğ, ı, ö, ş, ü)
   - Portuguese: o, a, de, que, e
   - Italian: il, la, di, che, e

3. MIXED LANGUAGE:
   - PRIMARY language = >50% of content
   - Mark MIXED: true if multiple languages significantly present

RESPONSE FORMAT (MUST follow exactly):
PRIMARY: [language_code]
CONFIDENCE: [0.0-1.0]
DETECTED: [comma-separated language codes]
MIXED: [true/false]

Now analyze this text:
{text}"""

def get_language_detection_prompt_config():
    """언어 감지 프롬프트 설정을 반환합니다."""
    return {
        "template": LANGUAGE_DETECTION_TEMPLATE
    }

def get_supported_languages():
    """지원하는 언어 목록을 반환합니다."""
    return SUPPORTED_LANGUAGES