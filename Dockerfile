# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ffmpeg \
    gnupg \
    xvfb \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libgtk-3-0 \
    # Data processing dependencies
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    # MeCab (Japanese text processing)
    mecab \
    libmecab-dev \
    libmecab2 \
    mecab-ipadic-utf8 \
    # Multilingual fonts for matplotlib
    fonts-nanum \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# 폰트 캐시 업데이트
RUN fc-cache -fv

# MeCab 설정
ENV MECAB_DICDIR=/var/lib/mecab/dic/ipadic-utf8
RUN ln -s /etc/mecabrc /usr/local/etc/mecabrc || true

# Google Chrome 저장소 추가 및 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Chrome 버전 확인
RUN google-chrome --version

# requirements 파일 복사 및 Python 패키지 설치 (의존성 해결 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # 불필요한 파일 정리로 이미지 크기 감소
    find /usr/local/lib/python3.11/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyo" -delete && \
    rm -rf /root/.cache

# 애플리케이션 코드 복사
COPY ./app ./app

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# 포트 노출
EXPOSE 14056

# Health check
HEALTHCHECK --interval=120s --timeout=600s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:14056/health || exit 1

CMD ["python", "-m", "app.main"]
