FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (Playwright용 포함)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    gnupg \
    # Playwright Chromium 의존성
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libdbus-1-3 \
    libexpat1 \
    libx11-6 \
    libxcb1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium 설치
RUN playwright install chromium

# 애플리케이션 코드 복사
COPY . .

# MCP 서버 경로 설정
ENV MCP_ROOT=/mcp-servers

# 포트 노출
EXPOSE 8000

# 기본 명령어 (docker-compose에서 오버라이드됨)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]