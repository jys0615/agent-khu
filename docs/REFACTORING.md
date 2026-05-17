# 리팩토링 로드맵 — LLM/SLM 하이브리드 + Azure Phi-4 Mini

> 작성일: 2026-05-17

---

## 배경 및 목적

### 현재 문제
- `rag_agent.py`: Elasticsearch BM25 검색 후 문서를 **그대로 반환** (Generation 없음 → 진짜 RAG 아님)
- `slm_agent.py`: Bllossom-8B 로컬 모델 코드가 있으나 **어디서도 호출되지 않음** (데드코드)
- `observability.py`: LLM 응답을 `agent-khu-interactions` 인덱스에 저장하지만, `khu-rag-knowledge`(RAG 검색 대상)에 **피드백되지 않음** → 연결 끊긴 파이프라인

### 목표
- **비용 절감**: Simple 질문은 Claude Sonnet 대신 Azure Phi-4 Mini(약 120x 저렴)로 처리
- **진짜 RAG 구현**: 검색(Retrieval) + 생성(Generation) 2단계 완성
- **지식 누적**: LLM 응답이 자동으로 RAG 지식베이스로 피드백되는 파이프라인 구축

---

## 목표 아키텍처

```
사용자 질문
    ↓
QuestionClassifier (기존 정규식 유지)
    │
    ├─ Simple → RAGAgent.search() → khu-rag-knowledge BM25 검색
    │                ↓ (docs 원문 반환)
    │           SLMAgent.generate(question, docs) → Azure Phi-4 Mini
    │                ↓
    │           응답 반환 (Claude 비용 없음)
    │
    └─ Complex → Claude Sonnet + MCP Tool-Use (기존 유지)
                        ↓
                   ObservabilityLogger
                   ├─ agent-khu-interactions (기존 로그)
                   └─ khu-rag-knowledge (신규: RAG 피드백) ← 핵심 추가
```

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/slm_agent.py` | 로컬 Bllossom → Azure Phi-4 Mini API |
| `backend/app/rag_agent.py` | `search()` 반환값에 `docs` 원문 추가 |
| `backend/app/agent/agent_loop.py` | Simple 경로: RAG 검색 → SLM 생성 연결 |
| `backend/app/observability.py` | LLM 응답 → `khu-rag-knowledge` 자동 인덱싱 추가 |
| `backend/app/agent/complex_handler.py` | Anthropic Prompt Caching 적용 |
| `backend/app/agent/tools_definition.py` | MCP Tool Annotations 추가 |
| `backend/requirements.txt` | `azure-ai-inference` 추가, `torch/transformers` 제거 |
| `.env.example` | Azure 환경변수 추가 |

---

## 최신 기술 트렌드 적용 항목

### 1. Azure AI Foundry — Phi-4 Mini Instruct (서버리스 API)
- Microsoft 자체 SLM, 로컬 GPU 없이 API로 호출
- 비용: 입력 $0.025/M 토큰, 출력 $0.05/M 토큰
- Azure 학생 크레딧으로 사용 가능

### 2. Anthropic Prompt Caching
- `complex_handler.py`의 system prompt에 `cache_control: {"type": "ephemeral"}` 적용
- 반복 호출 시 system prompt 토큰 ~80% 절감
- 코드 변경 2줄, 인프라 변경 없음

### 3. MCP Tool Annotations (2025 스펙)
- 도구 정의에 `readOnly`, `destructive` 메타데이터 추가
- LLM의 도구 선택 정확도 향상

---

## 제외 항목 (오버엔지니어링)

| 항목 | 제외 이유 |
|------|-----------|
| pgvector 마이그레이션 | ES 이미 작동 중, 교체 benefit 없음 |
| 시맨틱 라우터 | 정규식이 경희대 도메인에 충분 |
| LangGraph | 단일 에이전트에 불필요한 복잡도 |
| ES 벡터 검색 | BM25가 도메인 특화 쿼리에 충분 |
| 지속적 파인튜닝 | 운영 부담 대비 benefit 불명확 |

---

## SLM 설정 — GitHub Models (현재) / Azure AI Foundry (추후 전환)

### 현재: GitHub Models (무료)
- 경희대 Azure 테넌트 정책으로 AI Foundry 리소스 생성 불가 → GitHub Models로 대체
- 동일한 `azure-ai-inference` SDK 사용, 엔드포인트 URL만 다름
- 전환 시 환경변수 2개만 교체하면 됨

### 환경변수
```env
# GitHub Models (현재)
GITHUB_TOKEN=ghp_...

# Azure AI Foundry로 전환 시
# AZURE_AI_ENDPOINT=https://<resource>.services.ai.azure.com/models
# AZURE_AI_KEY=<api-key>
AZURE_SLM_MODEL=Phi-4-mini-instruct  # 동일
```

---

## 구현 완료 내역 (2026-05-17)

### 변경된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/slm_agent.py` | 로컬 Bllossom 제거 → GitHub Models Phi-4 Mini API (azure-ai-inference SDK) |
| `backend/app/rag_agent.py` | `search()` 반환값에 `docs` 원문 리스트 추가 (SLM 컨텍스트용) |
| `backend/app/agent/agent_loop.py` | Simple 경로: RAG 검색 → SLM 생성 2단계로 연결, `rag_slm` 라우팅 추가 |
| `backend/app/observability.py` | LLM 응답 성공 시 `khu-rag-knowledge`에 자동 인덱싱 (`_feed_to_rag`) |
| `backend/app/agent/complex_handler.py` | Anthropic Prompt Caching 적용 (system prompt에 `cache_control: ephemeral`) |
| `backend/app/agent/tools_definition.py` | MCP 2025 스펙 Tool Annotations 전 도구에 추가 |
| `backend/requirements.txt` | `azure-ai-inference==1.0.0b9` 추가 |
| `.env.example` | `GITHUB_TOKEN`, `AZURE_AI_*` 환경변수 추가 |

### 핵심 구현 포인트 (면접 활용)

**1. 진짜 RAG 완성**
- 기존: ES BM25 검색 → 문서 원문 그대로 반환 (Generation 없음)
- 변경: ES BM25 검색 → 검색 문서를 컨텍스트로 Phi-4 Mini에 주입 → 자연어 답변 생성
- Retrieval + Generation 2단계로 RAG 정의에 부합하는 구조 완성

**2. LLM → SLM 지식 피드백 파이프라인**
- 기존: LLM 응답이 `agent-khu-interactions`에만 로그로 저장 (활용 안 됨)
- 변경: Simple 질문의 성공한 LLM 응답 → `khu-rag-knowledge`에도 자동 인덱싱
- 시간이 지날수록 SLM이 처리할 수 있는 질문 범위 확대 → LLM 호출 비율 점진적 감소

**3. 비용 절감 구조**
- Simple 질문: Claude Sonnet($3/M) → Phi-4 Mini(무료~$0.025/M) ≈ 120배 절감
- Prompt Caching: system prompt 반복 청구 → 5분 캐시로 ~80% 절감
- 라우팅 레이블 `rag_slm` 추가 → Prometheus로 SLM 처리 비율 모니터링 가능

**4. MCP Tool Annotations (2025 스펙)**
- 전체 17개 도구에 `readOnly`, `destructive` 메타데이터 추가
- LLM이 도구 특성 파악 → 불필요한 도구 호출 감소
- 조회 전용 16개 / 상태 변경 1개(`reserve_seat`) 명시적 구분
