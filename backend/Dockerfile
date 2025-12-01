FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 설치 (브라우저 없이)
# MCP 서버들이 Playwright를 사용하지만, 대부분 requests로 대체 가능
# 실제 브라우저가 필요한 경우에만 아래 주석 해제
# RUN playwright install --with-deps chromium

# 애플리케이션 코드 복사
COPY . .

# MCP 서버 경로 설정
ENV MCP_ROOT=/mcp-servers

# Playwright를 사용하지 않고 requests로 크롤링하도록 설정
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 포트 노출
EXPOSE 8000

# 기본 명령어 (docker-compose에서 오버라이드됨)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]