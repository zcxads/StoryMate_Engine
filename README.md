# StoryMate Engine

## 프로젝트 개요

**StoryMate Engine**은 AI 기반 교육 콘텐츠 생성 플랫폼입니다. 다양한 AI 모델(OpenAI GPT, Google Gemini, Suno AI)을 활용하여 음성 합성, 텍스트 처리, 교육 콘텐츠 생성, 이미지 분석 등 종합적인 멀티모달 AI 서비스를 제공합니다.

### 역할
FastAPI 기반 API 서버로, 멀티 LLM 통합 및 교육 콘텐츠 자동 생성을 제공하며 WebSocket/SSE 기반 실시간 처리를 지원합니다.

### 기술 스택
- **Backend**: Python, FastAPI, Uvicorn
- **AI/ML**: LangChain, LangGraph, OpenAI (GPT-4o, TTS), Google Gemini (2.5/3.0)
- **Data Processing**: Selenium, BeautifulSoup, httpx
- **Infrastructure**: Docker, NCP Object Storage, WebSocket/SSE

## 주요 기능

- **음성 서비스**: TTS/STT, 배치 생성, 다국어 지원, 노래 생성 (Suno AI)
- **텍스트 처리**: 맞춤법 교정, 번역, 요약, 퀴즈 생성, 가사 작성, 연극 대본 생성, 언어 감지
- **이미지 분석**: 문제 풀이, 손가락 인식, 시각화
- **웹 크롤링**: 동적 콘텐츠 크롤링, 우클릭 방지 우회, 실시간 웹 검색

---

## 아키텍처 구조

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                        │
│                         (Mobile App)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Gateway                        │
│                   (app/main.py, port 14056)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Middleware: CORS, Error Handling, Logging           │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Router Layer                       │
│                    (app/api/router.py)                      │
│  ┌───────────┬────────────┬──────────────┬──────────────┐   │
│  │   TTS     │    STT     │ Orthography  │ Translation  │   │
│  ├───────────┼────────────┼──────────────┼──────────────┤   │
│  │   Quiz    │  Summary   │    Play      │   Lyrics     │   │
│  ├───────────┼────────────┼──────────────┼──────────────┤   │
│  │Explanation│  Crawler   │Visualization | Language Det.│   │
│  ├───────────┼────────────┼──────────────┼──────────────┤   │
│  │   Song    │Finger Det. |              │              │   |
│  └───────────┴────────────┴──────────────┴──────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│                 (app/services/...)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - 비즈니스 로직 처리                                   │  │
│  │  - LangChain/LangGraph 워크플로우                      │  │
│  │  - 데이터 검증 및 전처리                                │  │
│  │  - 파일 처리 (업로드/다운로드)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository/Integration Layer              │
│                (app/repositories/...)                       │
│  ┌────────────┬──────────────┬────────────┬──────────────┐  │
│  │  OpenAI    │   Gemini     │    NCP     │     Suno     │  │
│  ├────────────┼──────────────┼────────────┼──────────────┤  │
│  │ Selenium   │   httpx      │            │              │  |
│  └────────────┴──────────────┴────────────┴──────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                         │
│  ┌────────────┬──────────────┬────────────┬──────────────┐  │
│  │ OpenAI API │  Gemini API  │ NCP Object |   Suno API   |  | 
|  |            |              |  Storage   │              │  |
│  ├────────────┼──────────────┼────────────┼──────────────┤  │
│  │ LangSmith  │ Web Crawling │            │              |  |
│  │            │ Storage      │            |              │  │
│  └────────────┴──────────────┴────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Real-time Notification                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  WebSocket Manager ◄──► Clients                      │   │
│  │  SSE Stream        ◄──► Clients                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Persistent Storage                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud: NCP Object Storage (TTS, SONG)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 레이어별 설명

1. **Client Layer**: 클라이언트(모바일)에서 API 호출
2. **FastAPI Gateway**: 요청 라우팅, CORS, 에러 핸들링, 로깅
3. **API Router Layer**: 각 기능별 엔드포인트 정의 (app/api/v1/\*.py)
4. **Service Layer**: 비즈니스 로직 및 AI 워크플로우 처리
5. **Repository Layer**: 외부 API 및 서비스 통합
6. **External Services**: AI 모델 API, 클라우드 스토리지 등
7. **Real-time Notification**: WebSocket/SSE를 통한 실시간 알림
8. **Persistent Storage**: 로컬 파일 시스템 및 클라우드 스토리지

---

## Docker 배포 가이드라인

### 배포 단계

#### 1. 환경 설정
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집 - 아래 API 키 설정
# OPENAI_API_KEY=your_openai_api_key_here
# GEMINI_API_KEY=your_gemini_api_key_here
# (기타 NCP, Suno 등 설정)
```

#### 2. Docker 이미지 빌드 및 실행
```bash
# 컨테이너 빌드 및 시작
docker compose up -d --build

# 로그 확인
docker compose logs -f

# 서비스 상태 확인
docker compose ps
```

#### 3. 서비스 확인
```bash
# Health Check
curl http://localhost:14056/health

# API 문서 확인
# 브라우저에서 http://localhost:14056/docs 접속
```

#### 4. 컨테이너 관리
```bash
# 컨테이너 중지
docker compose down

# 컨테이너 재시작
docker compose restart

# 로그 확인
docker compose logs -f storymate-engine

# 컨테이너 내부 접속 (디버깅)
docker compose exec storymate-engine bash
```

## 주요 디렉토리 구조

```
C:\StoryMate\Engine/
│
├── app/                          # 메인 애플리케이션 디렉토리
│   ├── main.py                   # FastAPI 애플리케이션 엔트리포인트
│   ├── config.py                 # 환경 설정 및 상수
│   │
│   ├── api/                      # API 라우터 레이어
│   │   ├── router.py            # 통합 라우터 설정
│   │   └── v1/                  # API v1 엔드포인트
│   │       ├── tts.py           # TTS 서비스 API
│   │       ├── stt.py           # STT 서비스 API
│   │       ├── orthography.py   # 맞춤법 교정 API
│   │       ├── translation.py   # 번역 API
│   │       ├── quiz.py          # 퀴즈 생성 API
│   │       ├── summary.py       # 요약 API
│   │       ├── lyrics.py        # 가사 생성 API
│   │       ├── explanation.py   # 문제 풀이 API
│   │       ├── finger_detection.py  # 손가락 인식 API
│   │       ├── visualization.py # 시각화 API
│   │       ├── main_crawler.py  # 웹 크롤러 API
│   │       ├── play.py          # 연극 대본 API
│   │       ├── song.py          # 노래 생성 API
│   │       ├── language_detection.py # 언어 감지 API
│   │       └── content_category.py   # 콘텐츠 카테고리 API
│   │
│   ├── models/                  # Pydantic 데이터 모델
│   │   ├── voice/              # 음성 관련 모델 (TTS, STT)
│   │   ├── language/           # 언어 처리 모델
│   │   └── main_crawler/       # 메인 크롤러 모델
│   │
│   ├── services/                # 비즈니스 로직 레이어
│   │   ├── voice/              # 음성 서비스 (TTS/STT)
│   │   ├── language/           # 언어 처리 서비스
│   │   │   ├── orthography/    # 맞춤법 교정
│   │   │   ├── translation/    # 번역
│   │   │   ├── quiz/           # 퀴즈 생성
│   │   │   ├── summary/        # 요약
│   │   │   ├── lyrics/         # 가사 생성
│   │   │   ├── explanation/    # 문제 풀이
│   │   │   ├── finger_detection/ # 손가락 인식
│   │   │   ├── visualization/  # 시각화
│   │   │   └── play/           # 연극 대본
│   │   └── main_crawler/       # 메인 크롤러 서비스
│   │
│   ├── prompts/                 # LLM 프롬프트 템플릿
│   │   ├── voice/              # 음성 관련 프롬프트
│   │   ├── language/           # 언어 처리 프롬프트
│   │   │   ├── orthography/
│   │   │   ├── translation/
│   │   │   ├── quiz/
│   │   │   ├── summary/
│   │   │   ├── lyrics/
│   │   │   ├── explanation/
│   │   │   ├── finger_detection/
│   │   │   ├── visualization/
│   │   │   ├── play/
│   │   │   ├── language_detection/
│   │   │   └── content_category/
│   │   └── main_crawler/       # 크롤러 프롬프트
│   │
│   ├── repositories/            # 외부 API 통합 레이어
│   │   ├── tts/                # TTS API 통합
│   │   │   ├── base.py        # TTS 추상 베이스 클래스
│   │   │   ├── gemini_tts.py  # Gemini TTS 클라이언트
│   │   │   ├── openai_tts.py  # OpenAI TTS 클라이언트
│   │   │   └── utils.py       # TTS 유틸리티 (PCM→MP3 변환 등)
│   │   └── storage/           # 클라우드 스토리지 통합
│   │       └── ncp_storage.py # NCP Object Storage 클라이언트
│   │
│   └── utils/                   # 유틸리티 함수
│       ├── logger/             # 로깅 설정
│       ├── process_text.py     # 텍스트 처리 유틸
│       ├── timing.py           # 타이밍 측정
│       └── vectordb.py         # 벡터 DB 유틸
│
├── logs/                        # 로그 파일 디렉토리
│
├── .env.example                 # 환경 변수 예시
├── .gitignore                   # Git 무시 파일
├── .dockerignore                # Docker 무시 파일
├── Dockerfile                   # Docker 이미지 빌드 설정
├── docker-compose.yml           # Docker Compose 설정
├── requirements-dev.txt         # Python 의존성
└── README.md                    # 프로젝트 문서
```

---

## 로컬 개발 환경 설정

Docker 없이 로컬에서 직접 실행하는 방법입니다.

### 1. 사전 요구사항
- Python 3.11 이상
- pip 또는 poetry
- Google Chrome (크롤링 기능 사용 시)

### 2. 의존성 설치

```bash
# Python 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements-dev.txt

```

### 3. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집 - API 키 등 설정
```

### 4. 서버 실행

```bash
# 메인 애플리케이션 실행
python -m app.main

# 또는 uvicorn으로 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 14056 --reload
```

### 5. 서비스 확인

```bash
# Health Check
curl http://localhost:14056/health

# API 문서
# 브라우저에서 http://localhost:14056/docs 접속
```

---

## API 서비스 구조

### 1. 음성 (TTS/STT) 및 오디오 API

#### 1.1. 배치 TTS 생성 - POST `/api/v1/tts/generate/batch`
- 여러 텍스트를 동시에 음성으로 변환합니다.

#### 1.2. TTS 상태 조회 - GET `/api/v1/tts/jobs/{job_id}`
- 배치 TTS 작업의 진행 상태를 조회합니다.

#### 1.3. 연극 TTS 생성 - POST `/api/v1/tts/play/generate`
- 연극 대본의 각 대사를 음성으로 변환합니다.

#### 1.4. STT - POST `/api/v1/stt/transcribe-with-matching`
- 오디오 파일을 텍스트로 변환합니다.

#### 1.5. 노래 생성 - POST `/api/v1/song/generate`
- 제목과 가사로 AI 노래를 생성합니다 (Suno AI).

---

### 2. 텍스트 콘텐츠 생성 및 분석 API

#### 2.1. 텍스트 교정 - POST `/api/v1/orthography`
- 텍스트의 맞춤법, 띄어쓰기, 문법을 교정합니다.

#### 2.2. 연극 대본 생성 - POST `/api/v1/play/generate`
- 주제 또는 줄거리로 연극 대본을 생성합니다.

#### 2.3. 퀴즈 생성 - POST `/api/v1/quiz/`
- 텍스트 내용 기반으로 교육용 퀴즈를 생성합니다.

#### 2.4. 번역 - POST `/api/v1/translation/`
- 텍스트를 다른 언어로 번역합니다.

#### 2.5. 요약 - POST `/api/v1/summary/`
- 긴 텍스트나 책 내용을 요약합니다.

#### 2.6. 노래 가사 생성 - POST `/api/v1/lyrics/`
- 주제 또는 키워드로 노래 가사를 생성합니다.

#### 2.7. 언어 감지 - POST `/api/v1/language-detection/`
- 텍스트의 언어를 자동으로 감지합니다.

#### 2.8. 콘텐츠 카테고리 정의 - POST `/api/v1/content-category/analyze-text`
- 텍스트 내용을 분석하여 카테고리를 분류합니다.

#### 2.9. 웹 크롤링 - POST `/api/v1/main_crawler/crawl`
- 웹 URL로부터 본문 내용을 크롤링합니다.

---

### 3. 이미지 및 시각 인식 API

#### 3.1. 문제 풀이 - POST `/api/v1/explanation/`
- 이미지 속 문제(수학, 과학 등)를 분석하고 풀이합니다.

#### 3.2. 유사 문제 생성 - POST `/api/v1/explanation/similar`
- 주어진 문제 이미지와 유사한 문제를 생성합니다.

#### 3.3. 손가락 인식 - POST `/api/v1/finger-detection/analyze`
- 이미지에서 손가락이 가리키는 위치를 인식하고 해당 텍스트를 읽습니다.

#### 3.4. 시각화 - POST `/api/v1/visualization/generate`
- 텍스트 내용을 다이어그램, 차트 등으로 시각화합니다.

---

## 문제 해결

### 자주 발생하는 문제

1. **API 키 오류**
   ```
   해결: .env 파일에 올바른 API 키 설정
   ```

2. **포트 충돌**
   ```
   해결: docker-compose.yml에서 포트 변경
   ```

3. **Selenium 크롤링 실패**
   ```
   해결: Chrome/ChromeDriver 버전 확인, Docker 재빌드
   ```

4. **파일 업로드 실패**
   ```
   해결: NCP 설정 확인, 디스크 공간 점검
   ```

---

## API 문서

- **Swagger UI**: http://localhost:14056/docs
- **Health Check**: http://localhost:14056/health
