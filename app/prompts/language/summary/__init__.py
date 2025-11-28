"""
Summary prompts - Language-specific modules
"""

from langchain_core.prompts import PromptTemplate

# Import language-specific prompts
from .ko import KOREAN_SUMMARY_PROMPT
from .en import ENGLISH_SUMMARY_PROMPT
from .ja import JAPANESE_SUMMARY_PROMPT
from .zh import CHINESE_SUMMARY_PROMPT
from .es import SPANISH_SUMMARY_PROMPT
from .fr import FRENCH_SUMMARY_PROMPT
from .de import GERMAN_SUMMARY_PROMPT
from .it import ITALIAN_SUMMARY_PROMPT
from .pt import PORTUGUESE_SUMMARY_PROMPT
from .ru import RUSSIAN_SUMMARY_PROMPT
from .nl import DUTCH_SUMMARY_PROMPT
from .pl import POLISH_SUMMARY_PROMPT
from .vi import VIETNAMESE_SUMMARY_PROMPT
from .th import THAI_SUMMARY_PROMPT
from .id import INDONESIAN_SUMMARY_PROMPT
from .ar import ARABIC_SUMMARY_PROMPT
from .hi import HINDI_SUMMARY_PROMPT
from .tr import TURKISH_SUMMARY_PROMPT
from .ms import MALAY_SUMMARY_PROMPT
from .sv import SWEDISH_SUMMARY_PROMPT
from .no import NORWEGIAN_SUMMARY_PROMPT
from .da import DANISH_SUMMARY_PROMPT
from .fi import FINNISH_SUMMARY_PROMPT
from .hu import HUNGARIAN_SUMMARY_PROMPT
from .uk import UKRAINIAN_SUMMARY_PROMPT
from .el import GREEK_SUMMARY_PROMPT
from .ro import ROMANIAN_SUMMARY_PROMPT
from .cs import CZECH_SUMMARY_PROMPT
from .he import HEBREW_SUMMARY_PROMPT
from .fa import PERSIAN_SUMMARY_PROMPT
from .hr import CROATIAN_SUMMARY_PROMPT
from .be import BELARUSIAN_SUMMARY_PROMPT
from .hy import ARMENIAN_SUMMARY_PROMPT
from .az import AZERBAIJANI_SUMMARY_PROMPT
from .ca import CATALAN_SUMMARY_PROMPT
from .sr import SERBIAN_SUMMARY_PROMPT
from .bg import BULGARIAN_SUMMARY_PROMPT
from .sl import SLOVENIAN_SUMMARY_PROMPT
from .sk import SLOVAK_SUMMARY_PROMPT

# Language code mapping
LANGUAGE_CODES = {
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
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "ms": "Malay",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "hu": "Hungarian",
    "uk": "Ukrainian",
    "el": "Greek",
    "ro": "Romanian",
    "cs": "Czech",
    "he": "Hebrew",
    "fa": "Persian",
    "hr": "Croatian",
    "be": "Belarusian",
    "hy": "Armenian",
    "az": "Azerbaijani",
    "ca": "Catalan",
    "sr": "Serbian",
    "bg": "Bulgarian",
    "sl": "Slovenian",
    "sk": "Slovak",
}

# Default auto-detect prompt
SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""You are a professional content summarizer. You MUST respond in the EXACT SAME LANGUAGE as the input content.

**Content to Summarize:**
{book_content}

**CRITICAL LANGUAGE RULES:**
1. **DETECT INPUT LANGUAGE**: Analyze the language of the input content
2. **RESPOND IN SAME LANGUAGE**: You MUST respond in the EXACT SAME LANGUAGE as the input
3. **NO TRANSLATION**: Do NOT translate the content to any other language
4. **PRESERVE ORIGINAL LANGUAGE**: Keep the same language as the input text

**Summary Guidelines:**
1. **Length Guidelines**:
   - For 1-5 pages: 2-3 sentences
   - For 6-15 pages: 4-6 sentences (1-2 paragraphs)
   - For 16-30 pages: 6-10 sentences (2-3 paragraphs)
   - For 30+ pages: 8-12 sentences (3-4 paragraphs)
   - For web content (single page): 3-8 sentences depending on content length

2. **Content Guidelines**:
   - Summarize main themes, key events, and important messages
   - Include specific details and examples when relevant
   - Maintain the tone and style of the original content
   - Do not add commentary or analysis unless it's in the original
   - Be comprehensive but concise

**Current content has {page_count} pages.**

**FINAL REMINDER: You MUST respond in the EXACT SAME LANGUAGE as the input content. Do NOT translate.**

**Summary:**""")


def get_summary_prompt(language: str) -> PromptTemplate:
    """
    Get summary prompt for specified language

    Args:
        language: Language code (ko, en, ja, zh, etc.)

    Returns:
        PromptTemplate for the specified language. Falls back to auto-detect prompt if language not found.
    """
    language_prompts = {
        "ko": KOREAN_SUMMARY_PROMPT,
        "en": ENGLISH_SUMMARY_PROMPT,
        "ja": JAPANESE_SUMMARY_PROMPT,
        "zh": CHINESE_SUMMARY_PROMPT,
        "es": SPANISH_SUMMARY_PROMPT,
        "fr": FRENCH_SUMMARY_PROMPT,
        "de": GERMAN_SUMMARY_PROMPT,
        "it": ITALIAN_SUMMARY_PROMPT,
        "pt": PORTUGUESE_SUMMARY_PROMPT,
        "ru": RUSSIAN_SUMMARY_PROMPT,
        "nl": DUTCH_SUMMARY_PROMPT,
        "pl": POLISH_SUMMARY_PROMPT,
        "vi": VIETNAMESE_SUMMARY_PROMPT,
        "th": THAI_SUMMARY_PROMPT,
        "id": INDONESIAN_SUMMARY_PROMPT,
        "ar": ARABIC_SUMMARY_PROMPT,
        "hi": HINDI_SUMMARY_PROMPT,
        "tr": TURKISH_SUMMARY_PROMPT,
        "ms": MALAY_SUMMARY_PROMPT,
        "sv": SWEDISH_SUMMARY_PROMPT,
        "no": NORWEGIAN_SUMMARY_PROMPT,
        "da": DANISH_SUMMARY_PROMPT,
        "fi": FINNISH_SUMMARY_PROMPT,
        "hu": HUNGARIAN_SUMMARY_PROMPT,
        "uk": UKRAINIAN_SUMMARY_PROMPT,
        "el": GREEK_SUMMARY_PROMPT,
        "ro": ROMANIAN_SUMMARY_PROMPT,
        "cs": CZECH_SUMMARY_PROMPT,
        "he": HEBREW_SUMMARY_PROMPT,
        "fa": PERSIAN_SUMMARY_PROMPT,
        "hr": CROATIAN_SUMMARY_PROMPT,
        "be": BELARUSIAN_SUMMARY_PROMPT,
        "hy": ARMENIAN_SUMMARY_PROMPT,
        "az": AZERBAIJANI_SUMMARY_PROMPT,
        "ca": CATALAN_SUMMARY_PROMPT,
        "sr": SERBIAN_SUMMARY_PROMPT,
        "bg": BULGARIAN_SUMMARY_PROMPT,
        "sl": SLOVENIAN_SUMMARY_PROMPT,
        "sk": SLOVAK_SUMMARY_PROMPT,
    }

    # Fallback to auto-detect prompt if language not found
    return language_prompts.get(language, SUMMARY_PROMPT)


# Alias for backward compatibility
def get_language_specific_summary_prompt(language: str) -> PromptTemplate:
    """
    Backward compatibility alias for get_summary_prompt
    
    Args:
        language: Language code (ko, en, ja, zh, etc.)
        
    Returns:
        PromptTemplate for the specified language
    """
    return get_summary_prompt(language)


__all__ = [
    "SUMMARY_PROMPT",
    "KOREAN_SUMMARY_PROMPT",
    "ENGLISH_SUMMARY_PROMPT",
    "JAPANESE_SUMMARY_PROMPT",
    "CHINESE_SUMMARY_PROMPT",
    "SPANISH_SUMMARY_PROMPT",
    "FRENCH_SUMMARY_PROMPT",
    "GERMAN_SUMMARY_PROMPT",
    "ITALIAN_SUMMARY_PROMPT",
    "PORTUGUESE_SUMMARY_PROMPT",
    "RUSSIAN_SUMMARY_PROMPT",
    "DUTCH_SUMMARY_PROMPT",
    "POLISH_SUMMARY_PROMPT",
    "VIETNAMESE_SUMMARY_PROMPT",
    "THAI_SUMMARY_PROMPT",
    "INDONESIAN_SUMMARY_PROMPT",
    "ARABIC_SUMMARY_PROMPT",
    "HINDI_SUMMARY_PROMPT",
    "TURKISH_SUMMARY_PROMPT",
    "MALAY_SUMMARY_PROMPT",
    "SWEDISH_SUMMARY_PROMPT",
    "NORWEGIAN_SUMMARY_PROMPT",
    "DANISH_SUMMARY_PROMPT",
    "FINNISH_SUMMARY_PROMPT",
    "HUNGARIAN_SUMMARY_PROMPT",
    "UKRAINIAN_SUMMARY_PROMPT",
    "GREEK_SUMMARY_PROMPT",
    "ROMANIAN_SUMMARY_PROMPT",
    "CZECH_SUMMARY_PROMPT",
    "HEBREW_SUMMARY_PROMPT",
    "PERSIAN_SUMMARY_PROMPT",
    "CROATIAN_SUMMARY_PROMPT",
    "BELARUSIAN_SUMMARY_PROMPT",
    "ARMENIAN_SUMMARY_PROMPT",
    "AZERBAIJANI_SUMMARY_PROMPT",
    "CATALAN_SUMMARY_PROMPT",
    "SERBIAN_SUMMARY_PROMPT",
    "BULGARIAN_SUMMARY_PROMPT",
    "SLOVENIAN_SUMMARY_PROMPT",
    "SLOVAK_SUMMARY_PROMPT",
    "LANGUAGE_CODES",
    "get_summary_prompt",
    "get_language_specific_summary_prompt",
]
