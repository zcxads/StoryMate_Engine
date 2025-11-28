"""
OCR Orthography prompts - Language-specific modules
"""

# Import all language-specific prompts
from .ko import PROOFREADING_KO, CONTEXTUAL_KO
from .en import PROOFREADING_EN, CONTEXTUAL_EN
from .ja import PROOFREADING_JA, CONTEXTUAL_JA
from .zh import PROOFREADING_ZH, CONTEXTUAL_ZH
from .es import PROOFREADING_ES, CONTEXTUAL_ES
from .fr import PROOFREADING_FR, CONTEXTUAL_FR
from .de import PROOFREADING_DE, CONTEXTUAL_DE
from .it import PROOFREADING_IT, CONTEXTUAL_IT
from .pt import PROOFREADING_PT, CONTEXTUAL_PT
from .ru import PROOFREADING_RU, CONTEXTUAL_RU
from .nl import PROOFREADING_NL, CONTEXTUAL_NL
from .pl import PROOFREADING_PL, CONTEXTUAL_PL
from .sv import PROOFREADING_SV, CONTEXTUAL_SV
from .no import PROOFREADING_NO, CONTEXTUAL_NO
from .da import PROOFREADING_DA, CONTEXTUAL_DA
from .fi import PROOFREADING_FI, CONTEXTUAL_FI
from .cs import PROOFREADING_CS, CONTEXTUAL_CS
from .hu import PROOFREADING_HU, CONTEXTUAL_HU
from .ro import PROOFREADING_RO, CONTEXTUAL_RO
from .el import PROOFREADING_EL, CONTEXTUAL_EL
from .uk import PROOFREADING_UK, CONTEXTUAL_UK
from .sr import PROOFREADING_SR, CONTEXTUAL_SR
from .sk import PROOFREADING_SK, CONTEXTUAL_SK
from .sl import PROOFREADING_SL, CONTEXTUAL_SL
from .hr import PROOFREADING_HR, CONTEXTUAL_HR
from .bg import PROOFREADING_BG, CONTEXTUAL_BG
from .ca import PROOFREADING_CA, CONTEXTUAL_CA
from .ar import PROOFREADING_AR, CONTEXTUAL_AR
from .he import PROOFREADING_HE, CONTEXTUAL_HE
from .fa import PROOFREADING_FA, CONTEXTUAL_FA
from .tr import PROOFREADING_TR, CONTEXTUAL_TR
from .hi import PROOFREADING_HI, CONTEXTUAL_HI
from .vi import PROOFREADING_VI, CONTEXTUAL_VI
from .th import PROOFREADING_TH, CONTEXTUAL_TH
from .id import PROOFREADING_ID, CONTEXTUAL_ID
from .ms import PROOFREADING_MS, CONTEXTUAL_MS
from .be import PROOFREADING_BE, CONTEXTUAL_BE
from .hy import PROOFREADING_HY, CONTEXTUAL_HY
from .az import PROOFREADING_AZ, CONTEXTUAL_AZ

PROOFREADING_INPUT_VARIABLES = ["text"]
CONTEXTUAL_INPUT_VARIABLES = ["text", "original_text"]

def get_proofreading_prompt_config(language: str):
    """Get proofreading prompt configuration"""
    lang = language.lower().strip()
    
    proofreading_templates = {
        "ko": PROOFREADING_KO, "en": PROOFREADING_EN,
        "ja": PROOFREADING_JA, "zh": PROOFREADING_ZH,
        "es": PROOFREADING_ES, "fr": PROOFREADING_FR,
        "de": PROOFREADING_DE, "it": PROOFREADING_IT,
        "pt": PROOFREADING_PT, "ru": PROOFREADING_RU,
        "nl": PROOFREADING_NL, "pl": PROOFREADING_PL,
        "sv": PROOFREADING_SV, "no": PROOFREADING_NO,
        "da": PROOFREADING_DA, "fi": PROOFREADING_FI,
        "cs": PROOFREADING_CS, "hu": PROOFREADING_HU,
        "ro": PROOFREADING_RO, "el": PROOFREADING_EL,
        "uk": PROOFREADING_UK, "sr": PROOFREADING_SR,
        "sk": PROOFREADING_SK, "sl": PROOFREADING_SL,
        "hr": PROOFREADING_HR, "bg": PROOFREADING_BG,
        "ca": PROOFREADING_CA, "ar": PROOFREADING_AR,
        "he": PROOFREADING_HE, "fa": PROOFREADING_FA,
        "tr": PROOFREADING_TR, "hi": PROOFREADING_HI,
        "vi": PROOFREADING_VI, "th": PROOFREADING_TH,
        "id": PROOFREADING_ID, "ms": PROOFREADING_MS,
        "be": PROOFREADING_BE, "hy": PROOFREADING_HY,
        "az": PROOFREADING_AZ,
    }
    
    template = proofreading_templates.get(lang, PROOFREADING_KO)
    return {"template": template, "input_variables": PROOFREADING_INPUT_VARIABLES}


def get_contextual_prompt_config(language: str):
    """Get contextual prompt configuration"""
    lang = language.lower().strip()
    
    contextual_templates = {
        "ko": CONTEXTUAL_KO, "en": CONTEXTUAL_EN,
        "ja": CONTEXTUAL_JA, "zh": CONTEXTUAL_ZH,
        "es": CONTEXTUAL_ES, "fr": CONTEXTUAL_FR,
        "de": CONTEXTUAL_DE, "it": CONTEXTUAL_IT,
        "pt": CONTEXTUAL_PT, "ru": CONTEXTUAL_RU,
        "nl": CONTEXTUAL_NL, "pl": CONTEXTUAL_PL,
        "sv": CONTEXTUAL_SV, "no": CONTEXTUAL_NO,
        "da": CONTEXTUAL_DA, "fi": CONTEXTUAL_FI,
        "cs": CONTEXTUAL_CS, "hu": CONTEXTUAL_HU,
        "ro": CONTEXTUAL_RO, "el": CONTEXTUAL_EL,
        "uk": CONTEXTUAL_UK, "sr": CONTEXTUAL_SR,
        "sk": CONTEXTUAL_SK, "sl": CONTEXTUAL_SL,
        "hr": CONTEXTUAL_HR, "bg": CONTEXTUAL_BG,
        "ca": CONTEXTUAL_CA, "ar": CONTEXTUAL_AR,
        "he": CONTEXTUAL_HE, "fa": CONTEXTUAL_FA,
        "tr": CONTEXTUAL_TR, "hi": CONTEXTUAL_HI,
        "vi": CONTEXTUAL_VI, "th": CONTEXTUAL_TH,
        "id": CONTEXTUAL_ID, "ms": CONTEXTUAL_MS,
        "be": CONTEXTUAL_BE, "hy": CONTEXTUAL_HY,
        "az": CONTEXTUAL_AZ,
    }
    
    template = contextual_templates.get(lang, CONTEXTUAL_KO)
    return {"template": template, "input_variables": CONTEXTUAL_INPUT_VARIABLES}


__all__ = [
    "get_proofreading_prompt_config",
    "get_contextual_prompt_config",
    "PROOFREADING_INPUT_VARIABLES",
    "CONTEXTUAL_INPUT_VARIABLES",
]
