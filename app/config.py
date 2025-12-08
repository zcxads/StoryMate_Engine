import os
from typing import Optional, List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션 기본 설정
    app_name: str = "Engine"
    app_version: str = "1.0.0"
    debug: bool = False

    # 파일 저장 설정
    output_dir: str = "tts_output"

    # 언어 설정
    language_code: List[str] = ['ko', 'en', 'ja', 'zh']

    # mod by LAB (25.08.19)
    # TTS 모델 설정
    tts_model: str = "gemini-2.5-flash-preview-tts"
    audio_format: str = "mp3"
    openai_tts_model: str = "gpt-4o-mini-tts"

    # ============================================
    # 중앙화된 TTS 제공자 설정
    # ============================================
    # TTS 제공자 선택: "gemini", "openai", "murf"
    # 일반 TTS (배치 TTS 등)에서 사용할 기본 제공자
    # 이 값을 변경하면 일반 TTS의 제공자를 한 번에 변경할 수 있습니다.
    default_tts_provider: str = "openai"

    # 참고: 연극 TTS는 항상 Murf를 사용합니다.

    # TTS API 재시도 설정
    tts_max_retries: int = 3
    tts_base_delay: float = 2.0
    tts_rate_limit_delay: float = 5.0
    # mod by LAB (25.08.19) 

    # mod by LAB (25.08.19) 
    # 사용 가능한 목소리 설정
    gemini_all_voices: List[str] = [
        "Achernar",
        "Achird",
        "Algenib",
        "Alnilam",
        "Aoede",
        "Autonoe",
        "Callirrhoe",
        "Charon",
        "Despina",
        "Enceladus",
        "Erinome",
        "Fenrir",
        "Gacrux",
        "Iapetus",
        "Kore",
        "Laomedeia",
        "Leda",
        "Orus",
        "Puck",
        "Pulcherrima",
        "Rasalgethi",
        "Sadachbia",
        "Sadaltager",
        "Schedar",
        "Sulafat",
        "Umbriel",
        "Vindemiatrix",
        "Zephyr",
        "Zubenelgenubi",
    ]
    openai_all_voices: List[str] = [
        "alloy", "echo", "fable", "onyx", "nova", "shimmer"
    ]

    gemini_male_voices: List[str] = [
        "Achernar",
        "Achird",
        "Alnilam",
        "Charon",
        "Enceladus",
        "Fenrir",
        "Iapetus",
        "Orus",
        "Puck",
        "Rasalgethi",
        "Sadachbia",
        "Sadaltager",
        "Schedar",
        "Umbriel",
        "Zubenelgenubi",
    ]

    openai_male_voices: List[str] = [
        "echo", "fable", "onyx"
    ]

    gemini_female_voices: List[str] = [
        "Algenib",
        "Aoede",
        "Autonoe",
        "Callirrhoe",
        "Despina",
        "Erinome",
        "Gacrux",
        "Kore",
        "Laomedeia",
        "Leda",
        "Sulafat",
        "Vindemiatrix",
        "Zephyr",
    ]

    openai_female_voices: List[str] = [
        "nova", "shimmer"
    ]

    murfai_english_male_voices: List[str]   = ["en-US-terrell", "en-US-miles"]
    murfai_english_female_voices: List[str] = ["en-US-natalie", "en-US-riley"]
    murfai_japanese_male_voices: List[str] = ["ja-JP-kenji"]
    murfai_japanese_female_voices: List[str] = ["ja-JP-kimi"]
    murfai_korean_male_voices: List[str] = ["ko-KR-sanghoon"]
    murfai_korean_female_voices: List[str] = ["ko-KR-gyeong"]
    murfai_chinese_male_voices: List[str] = ["zh-CN-zhang"]
    murfai_chinese_female_voices: List[str] = ["zh-CN-jiao"]
    murfai_english_narrator_voice: str = "en-US-carter"
    murfai_korean_narrator_voice: str = "ko-KR-jong-su"
    murfai_japanese_narrator_voice: str = "ja-JP-denki"
    murfai_chinese_narrator_voice: str = "zh-CN-tao"

    # ============================================
    # 중앙화된 LLM 모델 설정
    # ============================================
    # 기본 LLM 제공자 (gemini, openai)
    default_llm_model: Optional[str] = "gemini-2.5-flash"

    # OpenAI 설정
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: Optional[str] = os.getenv("OPENAI_MODEL")
    openai_temperature: Optional[float] = 0.0
    openai_max_tokens: Optional[int] = 4000

    # Gemini 설정
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: Optional[str] = os.getenv("GEMINI_MODEL")
    gemini_temperature: Optional[float] = 0.0
    gemini_max_tokens: Optional[int] = 2048

    # ============================================
    # 기능별 LLM 모델 설정 (중앙 관리)
    # ============================================
    # 문제 풀이 전용 모델 (gemini-3-pro-preview 사용)
    llm_for_explanation: Optional[str] = "gemini-3-pro-preview"

    # 웹 크롤러 설정
    web_crawler_timeout: int = 30
    web_crawler_headless: bool = True
    web_crawler_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    web_crawler_window_size: str = "1920,1080"

    # LangChain/LangSmith 설정
    langchain_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY")

    langsmith_tracing: Optional[bool] = True
    langsmith_endpoint: Optional[str] = "https://api.smith.langchain.com"
    langsmith_api_key: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    langsmith_project: Optional[str] = "storymate"

    # 기타 설정 (model_ 접두사 제거)
    log_level: Optional[str] = "INFO"

    # NCP (Naver Cloud Platform) 설정
    naver_service_name: Optional[str] = "s3"
    naver_endpoint_url: Optional[str] = "https://kr.object.ncloudstorage.com"
    ncp_access_key: Optional[str] = os.getenv("ACCESS")
    ncp_secret_key: Optional[str] = os.getenv("SECRET")
    naver_bucket_name: Optional[str] = os.getenv("NAVER_BUCKET_NAME")
    naver_bucket_visual: Optional[str] = os.getenv("NAVER_BUCKET_VISUAL")
    naver_bucket_tts_folder: Optional[str] = "TTS"
    naver_bucket_play_folder: Optional[str] = "PLAY"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # 추가 필드 허용
        protected_namespaces=(),  # model_ 네임스페이스 보호 해제
    )


# 전역 설정 인스턴스
settings = Settings()
