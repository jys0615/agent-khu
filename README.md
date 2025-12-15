# Agent KHU 🎓

> **AI Agent 기반** 경희대학교 캠퍼스 정보 통합 시스템

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Agent KHU**는 [Anthropic Claude](https://www.anthropic.com/)와 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)을 활용하여 경희대학교 학생들에게 개인화된 캠퍼스 정보를 제공하는 AI 시스템입니다. Vision 기반 인식은 정확도를 위해 Opus 4.5 프롬프트로 개선되었습니다.

---

## ✨ 주요 기능

### Agentic AI
Claude Sonnet 4가 **자율적으로** 필요한 정보를 찾아 답변합니다
- **Tool-Use 패턴**: 상황에 맞는 MCP 서버를 자동 선택
- **컨텍스트 누적**: 최대 5회 반복으로 복잡한 질문 처리
- **자연어 이해**: 학생 의도 정확히 파악

### 개인화
학번, 학과, 관심분야 기반 맞춤형 정보
- **졸업요건 자동 계산**: 입학년도별 맞춤 요건
- **수강 추천**: 관심분야 기반 과목 제안
- **캠퍼스별 정보**: 서울/국제 캠퍼스 구분

### 🔌 MCP 표준 프로토콜
7개의 마이크로서비스가 협력하여 정보 제공. 현재 meal, shutle mcp는 작업 진행 중

| MCP 서버 | 기능 | 특징 |
|---------|------|------|
| **curriculum** | 교과과정 조회 | 24시간 자동 갱신, rowspan 처리 |
| **notice** | 공지사항 검색 | 실시간 크롤링, 키워드 필터링 |
| **course** | 수강신청 정보 | Playwright 자동화, 1시간 캐싱 |
| **library** | 도서관 좌석 | 실시간 현황, 예약 기능 |
| **meal** | 학식 메뉴 | 날짜별 조회, 메뉴 검색, 원본 링크 포함 |
| **shuttle** | 셔틀버스 | 실시간 도착 정보 |
| **classroom** | 강의실 위치 | 전자정보대학관 공간 검색 |

---

## 🚀 빠른 시작

### 요구사항
- **Python 3.9+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Docker** (선택, 권장)

### Docker Compose 실행 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/jys0615/agent-khu.git
cd agent-khu

# 2. 환경변수 설정
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# .env 파일 편집 (필수!)
# - ANTHROPIC_API_KEY: Claude API 키 (https://console.anthropic.com/)
# - DATABASE_URL: PostgreSQL 연결 정보

# 3. Docker Compose 실행
docker-compose up -d

# 4. 데이터베이스 초기화
docker-compose exec backend python init_db.py

# (선택) Playwright 브라우저 의존성 확인/재설치
# 컨테이너 내부에서 chromium 및 시스템 라이브러리 설치가 필요합니다.
# 본 저장소의 Dockerfile은 필요한 의존성을 설치하도록 구성되어 있습니다.

# 5. 접속
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 수동 설치

자세한 내용은 [설치 가이드](docs/INSTALLATION.md) 참고

---

## 💬 사용 예시

### 예시 1: 교과과정 조회
```
학생 (정윤서): "2019학번 컴공 학생인데 자료구조는 몇 학기에 들을 수 있어?"

Agent KHU:
📚 정윤서님, 자료구조 과목 정보를 안내해드리겠습니다!

📘 과목명: 자료구조
📝 과목코드: CSE204
⭐ 학점: 3학점
📋 분류: 전공 필수
📅 개설 학기: 1학기, 2학기

전공 필수 과목이므로 졸업을 위해 반드시 이수해야 합니다.
1학기와 2학기 모두 개설되므로 원하는 학기에 수강 가능합니다.
```

### 예시 2: 복합 질문
```
학생: "국제캠퍼스 도서관 자리 있어?"

Agent KHU:
[Tool: library-mcp 호출]

1. 도서관 ID / PW 입력

2. 도서관 좌석 현황
- 1열람실: 120석 중 45석 이용 가능
- 2열람실: 80석 중 12석 이용 가능
...

### 예시 3: 학식 메뉴 + 원본 링크
```
학생: 오늘 학식 알려줘

Agent KHU:
🍚 학생회관 학생식당 (중식)
- 메뉴: 깻잎제육덮밥
- 가격: 5,000원

원본 메뉴표 보기: https://khucoop.com/35 ↗
```
```

---

## 🏗️ 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                    사용자 (학생)                       │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  React Frontend       │  (Vite + TypeScript)
         │  - 채팅 인터페이스        │
         │  - 지도 렌더링           │
         └───────────┬───────────┘
                     │ HTTP/REST
         ┌───────────▼───────────┐
         │  FastAPI Backend      │  (Python)
         │  - JWT 인증            │
         │  - 세션 관리            │
         └───────────┬───────────┘
                     │
    ┌────────────────▼────────────────┐
    │  Agent (agent.py)               │
    │  - Claude Sonnet 4              │
    │  - Tool-Use Pattern             │
    │  - 최대 5회 반복                   │
    └────────────────┬────────────────┘
                     │
         ┌───────────▼───────────┐
         │  MCP Client           │  (JSON-RPC 2.0)
         │  - stdio 통신          │
         │  - 타임아웃 관리         │
         │  - Lazy start         │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌───────┐      ┌───────┐      ┌───────┐
│  MCP  │      │  MCP  │  ... │  MCP  │  (9개 서버)
│Server1│      │Server2│      │Server9│
└───┬───┘      └───┬───┘      └───┬───┘
    │              │              │
    ▼              ▼              ▼
┌─────────────────────────────────────┐
│  PostgreSQL / Web Crawling          │
└─────────────────────────────────────┘
```

### Agentic Workflow

```python
1. 사용자 질문 입력
    ↓
2. Claude가 Tool 선택 (자율 판단)
    ↓
3. MCP Client가 해당 서버 호출
    ↓
4. 결과를 Claude에게 전달
    ↓
5. Claude가 추가 Tool 필요 여부 판단
    ├─ 필요하면 → 2번으로 (최대 5회)
    └─ 불필요하면 → 최종 응답 생성
```

자세한 내용은 [아키텍처 문서](docs/ARCHITECTURE.md) 참고

---

## 문서

- **[설치 가이드](docs/INSTALLATION.md)** - 상세 설치 방법
- **[설정 가이드](docs/CONFIGURATION.md)** - 환경변수 및 설정
- **[API 문서](docs/API.md)** - REST API 엔드포인트
- **[MCP 서버 개발](docs/MCP_SERVERS.md)** - 새 MCP 서버 추가 방법
- **[아키텍처](docs/ARCHITECTURE.md)** - 시스템 구조 상세
- **[문제 해결](docs/TROUBLESHOOTING.md)** - 자주 발생하는 문제
- **[배포 가이드](docs/DEPLOYMENT.md)** - 프로덕션 배포

### 최근 변경 요약
- 학식 MCP: 주간 캐시 도입, Vision 정확도 향상 프롬프트, 원본 링크(`source_url`, `menu_url`) 반영
- Frontend: MealCard에서 링크 버튼 렌더링, 다크모드 UI 개선, 헤더 정리 및 드롭다운 테마 토글 추가
- Backend: `MealInfo` 스키마에 링크 필드 추가, 에러 처리 강화 및 CORS 문제 해결

### MCP 서버 문서
- [Curriculum MCP](mcp-servers/curriculum-mcp/README.md) - 교과과정 (rowspan 처리)
- [Notice MCP](mcp-servers/notice-mcp/README.md) - 공지사항
- [Course MCP](mcp-servers/course-mcp/README.md) - 수강신청 (Playwright)
- [Library MCP](mcp-servers/library-mcp/README.md) - 도서관
- [기타 서버들...](mcp-servers/)

---

## 🛠️ 기술 스택

### AI & Protocol
- **[Anthropic Claude Sonnet 4](https://www.anthropic.com/)** - AI 모델
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** - 표준 프로토콜
- **JSON-RPC 2.0** - 통신 프로토콜

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** - 웹 프레임워크
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM
- **[PostgreSQL](https://www.postgresql.org/)** - 데이터베이스
- **[Playwright](https://playwright.dev/)** - 웹 크롤링
- **[JWT](https://jwt.io/)** - 인증

### Frontend
- **[React 18](https://react.dev/)** - UI 라이브러리
- **[TypeScript](https://www.typescriptlang.org/)** - 타입 안정성
- **[Vite](https://vitejs.dev/)** - 빌드 도구
- **[TailwindCSS](https://tailwindcss.com/)** - 스타일링
- **[Axios](https://axios-http.com/)** - HTTP 클라이언트
- **브라우저 Credential Manager** - 로그인 정보 자동 저장

### MCP Servers
- **Python**: curriculum, meal, library, shuttle, classroom, notice
- **Node.js/TypeScript**: sitemcp, instagram

---

## 📊 프로젝트 구조

```
agent-khu/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py            # 진입점
│   │   ├── agent.py           # Claude AI Agent (핵심!)
│   │   ├── mcp_client.py      # MCP 클라이언트
│   │   ├── mcp_manager.py     # MCP 관리자
│   │   ├── auth.py            # JWT 인증
│   │   ├── models.py          # DB 모델
│   │   ├── schemas.py         # Pydantic 스키마
│   │   ├── crud.py            # DB CRUD
│   │   ├── database.py        # DB 설정
│   │   └── routers/           # API 라우터
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── profiles.py
│   │       ├── classrooms.py
│   │       └── notices.py
│   ├── requirements.txt       # Python 의존성
│   ├── .env.example           # 환경변수 템플릿
│   └── init_db.py             # DB 초기화
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── App.tsx            # 메인 컴포넌트
│   │   ├── components/        # UI 컴포넌트
│   │   │   └── ChatInterface.tsx
│   │   └── api/               # API 클라이언트
│   ├── package.json           # Node.js 의존성
│   └── .env.example
│
├── mcp-servers/                # MCP 서버들
│   ├── curriculum-mcp/        # 교과과정
│   │   ├── server.py
│   │   ├── scrapers/
│   │   │   └── curriculum_scraper.py
│   │   └── data/
│   │       └── curriculum_data.json
│   ├── notice-mcp/            # 공지사항
│   ├── meal-mcp/              # 학식
│   ├── library-mcp/           # 도서관
│   ├── shuttle-mcp/           # 셔틀버스
│   ├── classroom-mcp/         # 강의실
│   ├── course-mcp/            # 수강신청
│   ├── instagram-mcp/         # Instagram
│   └── sitemcp/               # 범용 크롤링
│
├── docker-compose.yml          # Docker 설정
├── README.md                   # 이 파일
├── LICENSE                     # MIT 라이선스
├── CONTRIBUTING.md             # 기여 가이드
└── docs/                       # 상세 문서
```

---

## Contribution

기여를 환영합니다! 다음과 같은 기여를 받습니다:

- 🐛 **버그 수정**: 버그를 발견하셨나요?
- ✨ **새 기능**: MCP 서버 추가, 기능 개선
- 📖 **문서 개선**: 오타, 설명 추가
- 🧪 **테스트**: 테스트 코드 작성

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) 참고

### 빠른 기여 가이드

1. Fork & Clone
```bash
git clone https://github.com/jys0615/agent-khu.git
```

2. 브랜치 생성
```bash
git checkout -b feature/your-feature
```

3. 개발 & 테스트
```bash
# 코드 작성
# 테스트 실행
```

4. Pull Request
```bash
git push origin feature/your-feature
# GitHub에서 PR 생성
```

---

## 🔒 보안

보안 취약점을 발견하셨다면 공개 이슈가 아닌 **이메일**로 제보해주세요.

- 📧 **이메일**: [jys0615234@gmail.com]
- 🔐 **암호화**: GPG 키 제공 가능

자세한 내용은 [SECURITY.md](SECURITY.md) 참고

---

## 📄 라이선스

이 프로젝트는 **MIT License** 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

```
MIT License

Copyright (c) 2025 [jys0615]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 감사의 말

- **[Anthropic](https://www.anthropic.com/)** - Claude AI 모델 제공
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - 표준 프로토콜
- **경희대학교 소프트웨어융합대학** - 프로젝트 지원
- **오픈소스 커뮤니티** - 라이브러리 및 도구

---

## 📞 문의

- **GitHub Issues**: [이슈 페이지](https://github.com/jys0615/agent-khu/issues)
- **이메일**: jys0615234@gmail.com

---

## ⭐ Star History

프로젝트가 마음에 드셨다면 ⭐ Star를 눌러주세요!

[![Star History Chart](https://api.star-history.com/svg?repos=jys0615/agent-khu&type=Date)](https://star-history.com/#jys0615/agent-khu&Date)

---

<div align="center">

**Made with ❤️ by jys0615**

[Documentation](docs/) • [Issues](https://github.com/jys0615/agent-khu/issues) • [Discussions](https://github.com/jys0615/agent-khu/discussions)

</div>

