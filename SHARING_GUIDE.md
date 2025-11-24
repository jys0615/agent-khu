# 리포지토리 공유 가이드 (Repository Sharing Guide)

이 문서는 agent-khu 리포지토리의 구조와 코드를 다른 사람들과 공유하는 다양한 방법을 설명합니다.

## 1. GitHub을 통한 공유

### 1.1 공개 리포지토리로 설정
- GitHub 리포지토리 설정에서 public으로 변경하면 누구나 코드를 볼 수 있습니다
- Settings → General → Danger Zone → Change repository visibility

### 1.2 특정 사용자에게 권한 부여
- Settings → Collaborators → Add people
- 사용자 이름이나 이메일로 협력자를 초대할 수 있습니다

### 1.3 README 작성
- 리포지토리의 README.md 파일을 통해 프로젝트 개요, 구조, 사용법을 설명합니다
- 현재 README.md는 비어있으므로 업데이트가 필요합니다

## 2. 리포지토리 구조 문서화

### 2.1 프로젝트 구조
```
agent-khu/
├── backend/           # Python 백엔드 서버
│   ├── app/          # 애플리케이션 코드
│   ├── requirements.txt
│   └── 초기화 스크립트들
├── frontend/         # React/TypeScript 프론트엔드
│   ├── src/         # 소스 코드
│   ├── package.json
│   └── 설정 파일들
├── mcp-servers/     # MCP 서버들
│   ├── classroom-mcp/
│   ├── course-mcp/
│   ├── curriculum-mcp/
│   ├── instagram-mcp/
│   ├── library-mcp/
│   ├── meal-mcp/
│   ├── notice-mcp/
│   ├── shuttle-mcp/
│   └── sitemcp/
└── docker-compose.yml
```

### 2.2 구조 시각화 명령어
리포지토리 구조를 확인하려면 다음 명령어를 사용하세요:

```bash
# tree 명령어 설치 (없는 경우)
# Ubuntu/Debian: sudo apt-get install tree
# macOS: brew install tree

# 전체 구조 보기 (node_modules 제외)
tree -L 3 -I 'node_modules|venv|__pycache__'

# 디렉토리만 보기
tree -d -L 2 -I 'node_modules|venv'
```

## 3. 코드 공유 방법

### 3.1 ZIP 파일로 다운로드
- GitHub 리포지토리 페이지에서 Code → Download ZIP
- 전체 코드를 압축 파일로 받을 수 있습니다

### 3.2 Git Clone
다른 사람이 리포지토리를 클론하려면:
```bash
git clone https://github.com/jys0615/agent-khu.git
```

### 3.3 특정 파일/폴더 공유
- GitHub에서 파일을 선택하고 "Raw" 또는 "Permalink"로 직접 링크를 공유
- 예: `https://github.com/jys0615/agent-khu/blob/main/README.md`

## 4. 문서화 추천 사항

### 4.1 README.md 업데이트
다음 내용을 포함하는 것을 권장합니다:
- 프로젝트 소개
- 주요 기능
- 설치 방법
- 사용 방법
- 각 폴더의 역할 설명
- 기여 가이드 (선택사항)

### 4.2 추가 문서
- `docs/` 폴더를 만들어 상세한 문서 작성
- API 문서
- 아키텍처 다이어그램
- 개발 가이드

## 5. 온라인 미리보기

### 5.1 GitHub Pages
- 프론트엔드를 GitHub Pages로 배포하여 데모 사이트 제공
- Settings → Pages에서 설정

### 5.2 CodeSandbox/StackBlitz
- GitHub 리포지토리를 CodeSandbox나 StackBlitz에서 바로 열어볼 수 있습니다
- URL: `https://codesandbox.io/s/github/jys0615/agent-khu`

## 6. 프레젠테이션

### 6.1 스크린샷/녹화
- 코드 하이라이트 스크린샷
- 실행 화면 녹화
- README에 이미지 추가

### 6.2 온라인 코드 뷰어
- [GitHub1s](https://github1s.com/jys0615/agent-khu) - VSCode 스타일로 브라우저에서 보기
- [Sourcegraph](https://sourcegraph.com/github.com/jys0615/agent-khu) - 코드 검색 및 탐색

## 7. 보안 고려사항

⚠️ **중요**: 코드를 공유하기 전에 확인하세요:
- API 키, 비밀번호 등 민감한 정보 제거
- `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- 개인정보나 내부 정보가 포함되지 않았는지 확인

## 추가 도움말

더 많은 정보는 다음을 참고하세요:
- [GitHub Docs - Managing repository settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features)
- [Writing good documentation](https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/)
