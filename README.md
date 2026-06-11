# Agent KHU 🎓

> **MCP 기반** 경희대학교 캠퍼스 정보 통합 AI Agent 시스템

[![CI](https://github.com/jys0615/agent-khu/actions/workflows/ci.yml/badge.svg)](https://github.com/jys0615/agent-khu/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-2025--03--26-purple.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Agent KHU**는 [Anthropic Claude](https://www.anthropic.com/)와 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)을 활용하여 경희대학교 학생들에게 개인화된 캠퍼스 정보를 제공하는 AI 시스템입니다.

---

## ✨ 주요 기능

### Agentic AI
Claude Sonnet 4가 **자율적으로** 필요한 정보를 찾아 답변
- **Tool-Use 루프**: 최대 8회 반복으로 복합 질문 처리
- **실시간 스트리밍**: SSE(Server-Sent Events) 기반 토큰 단위 응답
- **SLM 3계층 분류**: 단순 질문은 로컬 SLM(Ollama) → Groq → Claude 순 라우팅
- **세션 기억**: Redis 기반 대화 히스토리 (최근 5턴, 30분 TTL)

### 개인화
학번·학과·관심분야 기반 맞춤형 정보
- **졸업요건 자동 계산**: 입학년도별 맞춤 요건 (컴퓨터공학과 2019~2025학번)
- **캠퍼스별 정보**: 서울/국제 캠퍼스 구분

### 🔌 MCP Streamable HTTP (2025-03-26 표준)
7개의 독립 MCP 서버가 HTTP로 통신

| MCP 서버 | 포트 | 기능 | 캐시 TTL |
|---------|------|------|----------|
| **classroom** | 8101 | 강의실 위치 (DB 조회) | 24시간 |
| **notice** | 8102 | 공지사항 실시간 크롤링 | 2시간 |
| **meal** | 8103 | 학식 메뉴 (Vision AI 파싱) | 1시간 |
| **library** | 8104 | 도서관 좌석·예약 | 1분 |
| **course** | 8105 | 수강신청 정보 (Playwright) | 1시간 |
| **curriculum** | 8106 | 교과과정·졸업요건 | 24시간 |
| **shuttle** | 8107 | 셔틀버스 시간표 | 정적 |

---

## 🚀 빠른 시작

### 요구사항
- **Docker & Docker Compose**
- **Anthropic API Key**

### 실행

```bash
# 1. 저장소 클론
git clone https://github.com/jys0615/agent-khu.git
cd agent-khu

# 2. 환경변수 설정
cat > .env << EOF
POSTGRES_PASSWORD=yourpassword
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...          # 선택: SLM fallback용
EOF

# 3. 실행
docker compose up -d

# 4. Ollama SLM 모델 설치 (선택)
docker exec agent-khu-ollama ollama pull qwen2.5:1.5b

# 5. RAG 초기 데이터 시드
docker exec agent-khu-backend python scripts/seed_rag.py
```

접속:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 💬 사용 예시

```
학생: 오늘 학식 뭐야?
Agent KHU: 🍚 학생회관 학생식당 (중식)
           - 메뉴: 깻잎제육덮밥 / 5,000원
           원본 메뉴표: https://khucoop.com/35 ↗

학생: 도서관 자리 있어?
Agent KHU: 📚 현재 좌석 현황
           - 1열람실: 406석 중 128석 이용 가능
           - 2열람실: 326석 중 43석 이용 가능

학생: 컴퓨터공학과 졸업요건 알려줘
Agent KHU: 🎓 컴퓨터공학과 졸업요건 (2019학번 기준)
           - 총 이수학점: 140학점
           - 전공필수: 45학점 이상 ...

학생: 그럼 전공필수 중 이번 학기 개설된 과목은?  ← 세션 기억 활용
Agent KHU: 이전 대화 맥락을 기반으로 ...
```

---

## 🏗️ 아키텍처

```
사용자 브라우저
    │  SSE (text/event-stream)
    ▼
React Frontend (Vite + TypeScript)
    │  POST /api/chat/stream
    ▼
FastAPI Backend (port 8000)
    ├─ SLM Agent (Ollama → Groq → skip)   ← 단순 질문 처리
    ├─ RAG Agent (Elasticsearch BM25)      ← 지식베이스 검색
    └─ Claude Tool-Use 루프 (최대 8회)     ← 복합 질문 처리
         │  FastMCP Streamable HTTP
         ▼
┌─────────────────────────────────────────────┐
│  MCP Servers (port 8101~8107)               │
│  classroom / notice / meal / library /      │
│  course / curriculum / shuttle              │
└─────────────────────────────────────────────┘
    │
    ▼
PostgreSQL · Redis · Elasticsearch · 외부 웹사이트
```

### 메시지 처리 흐름

```
1. 요청 수신 → session_id로 Redis에서 대화 히스토리 로드
2. SLM 1차 분류 (qwen2.5:1.5b)
   ├─ simple → RAG 검색 → 즉시 응답
   └─ complex → Claude Tool-Use 루프
3. Claude: [히스토리 + 현재 질문] → tool 선택 → MCP HTTP 호출
4. 결과 수신 → Claude에 전달 → 반복 (최대 8회)
5. 응답 완료 → Redis에 대화 1턴 저장 (TTL 30분)
```

---

## 🛠️ 기술 스택

### AI & Protocol
- **Claude Sonnet 4.6** — Tool-Use, 실시간 스트리밍
- **FastMCP 2.14.7** — MCP Streamable HTTP 서버
- **Ollama (qwen2.5:1.5b)** — 로컬 SLM (Layer 2)
- **Groq** — 클라우드 SLM fallback (Layer 3)
- **MCP 2025-03-26** — Model Context Protocol 표준

### Backend
- **FastAPI** — 비동기 웹 프레임워크
- **SQLAlchemy + PostgreSQL** — ORM + DB
- **Redis** — 도구 결과 캐시 + 세션 기억
- **Elasticsearch** — RAG 지식베이스 (BM25)
- **Playwright** — 수강신청 사이트 스크래핑
- **APScheduler** — 백그라운드 캐시 워밍업

### Frontend
- **React 18 + TypeScript** — UI
- **Vite** — 빌드 도구
- **TailwindCSS** — 스타일링
- **SSE (EventSource)** — 실시간 스트리밍 수신

### DevOps
- **Docker Compose** — 전체 스택 오케스트레이션 (11개 서비스)
- **GitHub Actions** — CI (lint → test → build) / CD (GHCR 이미지 배포)
- **GitHub Container Registry** — Docker 이미지 저장소

---

## 📊 프로젝트 구조

```
agent-khu/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── agent_loop.py        # Simple/Complex 라우팅
│   │   │   ├── complex_handler.py   # Claude Tool-Use 루프
│   │   │   ├── tool_executor.py     # MCP tool 호출
│   │   │   ├── tools_definition.py  # Tool 스키마
│   │   │   └── result_builder.py    # 응답 구성
│   │   ├── routers/
│   │   │   └── chat_stream.py       # SSE 스트리밍 엔드포인트
│   │   ├── cache.py                 # Redis (캐시 + 세션 기억)
│   │   ├── mcp_client.py            # FastMCP HTTP 클라이언트
│   │   ├── slm_agent.py             # SLM 3계층 분류기
│   │   ├── rag_agent.py             # RAG (Elasticsearch)
│   │   └── question_classifier.py  # 질문 분류
│   └── scripts/
│       └── seed_rag.py              # RAG 초기 데이터 시드
│
├── mcp-servers/
│   ├── classroom-mcp/   (port 8101)
│   ├── notice-mcp/      (port 8102)
│   ├── meal-mcp/        (port 8103)
│   ├── library-mcp/     (port 8104)
│   ├── course-mcp/      (port 8105)
│   ├── curriculum-mcp/  (port 8106)
│   └── shuttle-mcp/     (port 8107)
│
├── frontend/
│   └── src/
│       ├── components/ChatInterface.tsx
│       └── api/chat.ts
│
├── docker-compose.yml        # 로컬 개발 (Ollama 포함)
├── docker-compose.prod.yml   # 프로덕션 (Ollama 제외, 외부 DB)
├── azure/
│   ├── setup.sh              # Azure 리소스 생성 스크립트
│   └── DEPLOY.md             # 배포 가이드
└── docs/
    └── TROUBLESHOOTING.md
```

---

## 📄 라이선스

MIT License — [LICENSE](LICENSE) 참고

---

## 📞 문의

- **GitHub Issues**: [이슈 페이지](https://github.com/jys0615/agent-khu/issues)
- **이메일**: jys0615234@gmail.com

---

<div align="center">

**Made with ❤️ by jys0615**

</div>
