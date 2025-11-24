# agent-khu

경희대학교(KHU) 관련 서비스를 제공하는 MCP(Model Context Protocol) 서버 기반 에이전트 시스템입니다.

## 📁 프로젝트 구조

```
agent-khu/
├── backend/              # Python 백엔드 서버
│   ├── app/             # 메인 애플리케이션
│   ├── requirements.txt # Python 의존성
│   └── init_*.py        # 데이터베이스 초기화 스크립트
│
├── frontend/            # React + TypeScript 프론트엔드
│   ├── src/            # 소스 코드
│   ├── package.json    # Node.js 의존성
│   └── vite.config.ts  # Vite 설정
│
├── mcp-servers/        # MCP 서버 모듈들
│   ├── classroom-mcp/  # 강의실 정보
│   ├── course-mcp/     # 강의 정보
│   ├── curriculum-mcp/ # 교과과정
│   ├── instagram-mcp/  # Instagram 연동
│   ├── library-mcp/    # 도서관 정보
│   ├── meal-mcp/       # 학식 정보
│   ├── notice-mcp/     # 공지사항
│   ├── shuttle-mcp/    # 셔틀버스 정보
│   └── sitemcp/        # 사이트 관련 기능
│
└── docker-compose.yml  # Docker 설정

```

## 🚀 시작하기

### Backend 실행
```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

### Frontend 실행
```bash
cd frontend
npm install
npm run dev
```

### Docker로 실행
```bash
docker-compose up
```

## 📚 문서

- [리포지토리 공유 가이드](SHARING_GUIDE.md) - 이 프로젝트를 다른 사람과 공유하는 방법

## 🤝 기여하기

이슈와 풀 리퀘스트를 환영합니다!

## 📄 라이선스

이 프로젝트의 라이선스 정보는 별도로 명시되지 않았습니다.

