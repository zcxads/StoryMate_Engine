from fastapi import APIRouter

from app.api.v1.tts import router as tts_router
from app.api.v1.stt import router as stt_router
from app.api.v1.orthography import router as orthography_router
from app.api.v1.sound import router as sound_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.lyrics import router as lyrics_router
from app.api.v1.translation import router as translation_router
from app.api.v1.summary import router as summary_router
from app.api.v1.question import router as question_router
from app.api.v1.explanation import router as explanation_router
from app.api.v1.search import router as search_router
from app.api.v1.all import router as all_router
from app.api.v1.main_crawler import router as main_crawler_router
from app.api.v1.crawler_analysis import router as crawler_analysis_router
from app.api.v1.character import router as character_router
from app.api.v1.song import router as song_router
from app.api.v1.language_detection import router as language_detection_router
from app.api.v1.content_category import router as content_category_router
from app.api.v1.finger_detection import router as finger_detection_router
from app.api.v1.visualization import router as visualization_router
from app.api.v1.crawler import router as crawler_router
from app.api.v1.play import router as play_router


api_prefix = "/api/v1"

def get_integrated_router():
    integrated_router = APIRouter()
    
    integrated_router.include_router(
        tts_router,
        prefix=api_prefix,
        tags=["TTS 서비스"]
    )

    integrated_router.include_router(
        stt_router,
        prefix=api_prefix,
        tags=["STT 서비스"]
    )

    integrated_router.include_router(
        orthography_router,
        prefix=api_prefix,
        tags=["텍스트 처리 서비스"]
    )
    
    # integrated_router.include_router(
    #     sound_router,
    #     prefix=api_prefix,
    #     tags=["사운드 생성 서비스"]
    # )
    
    integrated_router.include_router(
        quiz_router,
        prefix=api_prefix,
        tags=["퀴즈 생성 서비스"]
    )
    
    integrated_router.include_router(
        lyrics_router,
        prefix=api_prefix,
        tags=["가사 생성 서비스"]
    )
    
    integrated_router.include_router(
        translation_router,
        prefix=api_prefix,
        tags=["번역 서비스"]
    )
    
    integrated_router.include_router(
        summary_router,
        prefix=api_prefix,
        tags=["요약 생성 서비스"]
    )
    
    integrated_router.include_router(
        question_router,
        prefix=api_prefix,
        tags=["질문 생성 서비스"]
    )
    
    integrated_router.include_router(
        explanation_router,
        prefix=api_prefix,
        tags=["문제 풀이 서비스"]
    )
    
    integrated_router.include_router(
        search_router,
        prefix=api_prefix,
        tags=["웹 검색 서비스"]
    )
    
    # integrated_router.include_router(
    #     all_router,
    #     prefix=api_prefix,
    #     tags=["통합 처리 서비스"]
    # )
    
    integrated_router.include_router(
        main_crawler_router,
        prefix=api_prefix,
        tags=["메인 크롤러 서비스"]
    )

    integrated_router.include_router(
        crawler_analysis_router,
        prefix=api_prefix,
        tags=["크롤러 분석 서비스"]
    )

    # integrated_router.include_router(
    #     crawler_router,
    #     prefix=api_prefix,
    #     tags=["시각화 서비스"]
    # )

    integrated_router.include_router(
        character_router,
        prefix=api_prefix,
        tags=["캐릭터 서비스"]
    )
    
    integrated_router.include_router(
        song_router,
        prefix=api_prefix,
        tags=["노래 생성 서비스"]
    )
    
    integrated_router.include_router(
        language_detection_router,
        prefix=api_prefix,
        tags=["언어 감지 서비스"]
    )
    
    integrated_router.include_router(
        content_category_router,
        prefix=api_prefix,
        tags=["콘텐츠 카테고리 서비스"]
    )
    
    integrated_router.include_router(
        finger_detection_router,
        prefix=api_prefix,
        tags=["손가락 인식 서비스"]
    )

    integrated_router.include_router(
        visualization_router,
        prefix=api_prefix,
        tags=["시각화 생성 서비스"]
    )
    
    integrated_router.include_router(
        play_router,
        prefix=api_prefix,
        tags=["연극 서비스"]
    )
    
    return integrated_router