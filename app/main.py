from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os

from app.core.config import settings
from app.api.router import get_integrated_router
# 로깅 설정
from app.utils.logger.setup import setup_logger
logger = setup_logger('main')

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description="StoryMate API - AI 기반 교육 콘텐츠 생성 플랫폼",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 통합 API 라우터 등록
integrated_router = get_integrated_router()
app.include_router(integrated_router)

@app.get("/")
async def root():
    """루트 경로 - API 문서로 리다이렉트"""
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """전체 애플리케이션 상태 확인"""
    
    # OpenAI API 키 확인
    api_key_configured = bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here")
    
    # Gemini API 키 확인
    gemini_key_configured = bool(os.getenv("GEMINI_API_KEY", os.getenv("GEMINI")))
    
    # 출력 디렉토리 확인
    output_dir_exists = os.path.exists(settings.output_dir)
    
    return {
        "status": "healthy" if (api_key_configured or gemini_key_configured) else "configuration_required",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "api_key_configured": api_key_configured,
        "gemini_key_configured": gemini_key_configured,
        "output_directory_exists": output_dir_exists,
        "output_directory": settings.output_dir,
        "features": {
            "realtime_notifications": True,
            "websocket_support": True,
            "sse_support": True,
            "ocr_processing": True,
            "speech_to_text": True,
            "quiz_generation": True,
            "lyrics_generation": True,
            "translation": True,
            "integrated_processing": True,
            "main_crawler": True,
            "async_explanation": True
        },
        "available_endpoints": [
            "/docs - API 문서",
            # TTS 엔드포인트
            "/api/v1/tts/voices - 사용 가능한 목소리 목록",
            "/api/v1/tts/generate - 단일 TTS 생성",
            "/api/v1/tts/generate/batch - 배치 TTS 생성",
            "/api/v1/tts/jobs/{job_id} - 작업 상태 조회",
            "/api/v1/tts/jobs/{job_id}/ws - WebSocket 실시간 알림",
            "/api/v1/tts/jobs/{job_id}/stream - SSE 실시간 스트림",
            "/api/v1/tts/files - 생성된 파일 목록",
            # "/api/v1/tts/download/{filename} - 파일 다운로드",
            "/api/v1/tts/notifications/stats - 실시간 알림 연결 통계",
            # STT 엔드포인트
            "/api/v1/stt/languages - 지원되는 STT 언어 목록",
            "/api/v1/stt/transcribe-file - 오디오 파일 업로드 및 텍스트 변환",
            "/api/v1/stt/health - STT 서비스 상태 확인",
            # 언어 처리 엔드포인트
            "/api/v1/orthography/ - 텍스트 전처리 및 교정",
            "/api/v1/quiz/ - 퀴즈 생성",
            "/api/v1/lyrics/ - 노래 가사 생성",
            "/api/v1/translation/ - 텍스트 번역",
            "/api/v1/language-detection/ - 텍스트 언어 감지",
            "/api/v1/summary/ - 책 내용 요약 생성",
            "/api/v1/question/ - 책 내용 기반 추천 질문 생성",
            # 문제 해결 엔드포인트 (개선됨)
            "/api/v1/explanation/ - 이미지 기반 문제 해결",
            "/api/v1/explanation/similar - 이미지 기반 유사 문제 생성",
            # 손가락 인식 및 문서 읽기 엔드포인트
            "/api/v1/finger-detection/models - 지원되는 AI 모델 목록",
            "/api/v1/finger-detection/analyze - 멀티모드 이미지 분석 (finger_detection | document_reading)",
            "/api/v1/finger-detection/analyze-upload - 파일 업로드 + 모드 선택 분석",
            "/api/v1/finger-detection/convert-to-base64 - 이미지 파일을 Base64로 변환",
            "/api/v1/finger-detection/health - 손가락 인식 및 문서 읽기 서비스 상태",
            # 문서 처리 엔드포인트
            "/api/v1/main_crawler/crawl - 웹사이트 본문 내용 크롤링",
            "/api/v1/main_crawler/health - 메인 크롤러 서비스 상태",
            # Song 엔드포인트
            "/api/v1/song/generate - 제목과 가사로 노래 생성",
            "/api/v1/song/health - 노래 서비스 상태",
            # Visualization 엔드포인트
            "/api/v1/visualization/models - 지원되는 시각화 모델 목록",
            "/api/v1/visualization/generate - 문서 시각화 생성",
            # 헬스체크 엔드포인트
            "/api/v1/orthography/health - 텍스트 교정 서비스 상태",
            "/api/v1/quiz/health - 퀴즈 서비스 상태",
            "/api/v1/lyrics/health - 가사 서비스 상태",
            "/api/v1/translation/health - 번역 서비스 상태",
            "/api/v1/language-detection/health - 언어 감지 서비스 상태",
            "/api/v1/summary/health - 요약 서비스 상태",
            "/api/v1/stt/health - STT 서비스 상태",
            "/api/v1/explanation/health - 문제 해결 서비스 상태",
            "/api/v1/finger-detection/health - 손가락 인식 및 문서 읽기 서비스 상태",
            "/api/v1/main_crawler/health - 메인 크롤러 서비스 상태",
            "/api/v1/song/health - 노래 서비스 상태",
            "/api/v1/visualization/health - 시각화 서비스 상태"
        ]
    }

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 시작됨")
    logger.info(f"📁 출력 디렉토리: {settings.output_dir}")
    logger.info(f"📡 실시간 알림 지원: WebSocket + SSE")
    logger.info(f"🎯 지원 기능: TTS, STT, Orthography, Quiz, Lyrics, Translation, Language Detection, Summary, Explanation, Main Crawler, Song, Visualization")
    
    # 출력 디렉토리 생성
    os.makedirs(settings.output_dir, exist_ok=True)
    
    # API 키 확인
    openai_key = settings.openai_api_key
    gemini_key = os.getenv("GEMINI_API_KEY", os.getenv("GEMINI"))
    
    if not openai_key or openai_key == "your_openai_api_key_here":
        logger.warning("⚠️ 경고: OpenAI API 키가 설정되지 않았습니다.")
    else:
        logger.info("✅ OpenAI API 키가 구성되었습니다.")
    
    if not gemini_key:
        logger.warning("⚠️ 경고: Gemini API 키가 설정되지 않았습니다.")
        logger.warning("   .env 파일에서 GEMINI_API_KEY 또는 GEMINI을 설정해주세요.")
    else:
        logger.info("✅ Gemini API 키가 구성되었습니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(f"🛑 {settings.app_name} 종료됨")
    
    # Selenium WebDriver 정리
    try:
        from app.services.main_crawler.web_crawler import MainCrawlerAgent
        MainCrawlerAgent.cleanup()  # 정적 메서드 호출
        logger.info("🧹 Selenium WebDriver 정리 완료")
    except Exception as e:
        logger.error(f"⚠️ Selenium WebDriver 정리 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=14056,
        reload=settings.debug,
        log_level="info",
        # 🚀 타임아웃 설정 대폭 증가 (무제한에 가깝게)
        timeout_keep_alive=7200,  # 2시간
        timeout_graceful_shutdown=60,  # 60초
        access_log=True,
        # 워커 설정
        workers=1,  # 비동기 작업 때문에 1개로 제한
        # 추가 설정 - limit 파라미터들 제거 (None이나 생략하면 무제한)
        loop="asyncio"
    )
