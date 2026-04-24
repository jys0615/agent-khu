# 아키텍처 업데이트 (2025-12) 📐

Agent KHU 시스템 아키텍처의 최신 변경사항을 설명합니다.

---

## 🆕 주요 변경사항

### 1. Hybrid LLM/SLM 아키텍처

**개요**: Question Classifier를 통해 질문을 Simple/Complex로 분류하고, Simple 질문은 SLM으로 라우팅하여 응답 속도를 85% 개선했습니다.

```
┌─────────┐
│  질문   │
└────┬────┘
     │
     ▼
┌──────────────────┐
│ Question         │
│ Classifier       │  (패턴 매칭 + 휴리스틱)
└────┬─────────────┘
     │
     ├─ simple ──→ ┌───────┐  confidence >= 0.7?
     │             │  SLM  │  ─────────────────┐
     │             └───────┘                   │
     │                 │                        │
     │                 │ confidence < 0.7       │
     │                 ▼                        │
     └─ complex ───→ ┌────────────┐            │
                     │  LLM       │ ◄──────────┘
                     │  (Claude)  │  fallback
                     └────────────┘
                           │
                           ▼
                      최종 응답
```

**Question Classifier 로직** (`question_classifier.py`):

```python
class QuestionClassifier:
    SIMPLE_PATTERNS = [
        r"몇\s*학점", r"언제", r"시간", r"어디", r"위치",
        r"메뉴", r"식단", r"좌석", r"도서관", r"강의실"
    ]

    COMPLEX_PATTERNS = [
        r"추천", r"비교", r"분석", r"평가", r"졸업\s*요건",
        r"계획", r"전략", r"어떻게", r"왜"
    ]

    def classify(self, question: str) -> Literal["simple", "complex"]:
        # 1. Complex 패턴 우선 체크
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, question):
                return "complex"

        # 2. Simple 패턴 체크
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, question):
                return "simple"

        # 3. 휴리스틱 (질문 길이, 물음표 개수)
        if len(question) > 50 or question.count("?") > 1:
            return "complex"

        return "simple"  # 기본값
```

**라우팅 로직** (`agent_loop.py`):

```python
async def chat_with_claude_async(message: str, ...):
    # 질문 분류
    question_type = classifier.classify(message)

    # Simple 질문 → SLM 시도
    if question_type == "simple":
        slm = get_slm_agent()
        if slm.enabled:
            slm_result = await slm.generate(message)

            if slm_result["success"] and slm_result["confidence"] >= 0.7:
                # SLM 성공 → 즉시 반환 (평균 1s)
                return {"message": slm_result["message"]}
            else:
                # SLM 실패 → LLM Fallback
                routing_decision = "llm_fallback"

    # Complex 질문 또는 SLM 실패 → LLM 사용
    # ... (Claude API 호출)
```

**성능 개선**:
- Simple 질문: 7s → 1s (**-85%**)
- SLM 신뢰도 임계값: 0.7 (조정 가능)
- Fallback 비율: 약 15-20%

---

### 2. Observability 시스템

**개요**: Elasticsearch 기반으로 모든 사용자 상호작용을 로깅하여 메트릭 수집 및 학습 데이터 축적.

```
┌─────────────────────────────────────┐
│  Agent Interaction                  │
│  - question                         │
│  - user_id                          │
│  - question_type (simple/complex)   │
│  - routing_decision (llm/slm/...)   │
│  - mcp_tools_used []                │
│  - response                         │
│  - latency_ms                       │
│  - success (bool)                   │
└──────────────┬──────────────────────┘
               │
               ▼
      ┌────────────────┐
      │ Elasticsearch  │
      │ Index:         │
      │ agent-khu-     │
      │ interactions   │
      └────────────────┘
               │
               ▼
      ┌────────────────┐
      │ 메트릭 분석     │
      │ - 응답시간 추이  │
      │ - 라우팅 비율    │
      │ - Tool 사용량    │
      │ - 성공률        │
      └────────────────┘
```

**로깅 코드** (`observability.py`):

```python
class ObservabilityLogger:
    async def log_interaction(
        self,
        question: str,
        user_id: str,
        question_type: str,  # "simple" or "complex"
        routing_decision: str,  # "llm", "slm", "llm_fallback"
        mcp_tools_used: List[str],
        response: str,
        latency_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ):
        doc = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "user_id": user_id,
            "question_type": question_type,
            "routing_decision": routing_decision,
            "mcp_tools_used": mcp_tools_used,
            "response": response,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_message
        }

        await self.es.index(
            index=self.index_name,
            document=doc,
            refresh=False  # 성능 향상
        )
```

**활용 방안**:
- **SLM 학습 데이터**: Simple 질문 + 응답 쌍 수집
- **성능 모니터링**: P50/P95/P99 레이턴시 추적
- **A/B 테스팅**: 라우팅 전략 비교
- **오류 추적**: 실패한 질문 패턴 분석

---

### 3. Redis 캐싱 확대

**개요**: Tool별 캐시 TTL을 조정하여 반복 쿼리 응답 속도를 최대 80% 개선.

**캐시 TTL 설정** (`tools_definition.py`):

```python
CACHE_TTL = {
    # 자주 변하지 않는 데이터 (24시간)
    "search_classroom": 86400,
    "search_curriculum": 86400,
    "get_requirements": 86400,
    "get_cafeteria_info": 86400,

    # 주기적 업데이트 데이터 (2시간)
    "search_notices": 7200,
    "get_latest_notices": 7200,

    # 자주 변하는 데이터 (1시간)
    "get_library_info": 3600,
    "evaluate_progress": 3600,
    "get_today_meal": 3600,

    # 실시간 데이터 (1분)
    "get_seat_availability": 60,
}
```

**캐시 키 생성** (`cache.py`):

```python
class CacheManager:
    def _make_key(self, prefix: str, **kwargs) -> str:
        # kwargs를 정렬하여 일관된 키 생성
        sorted_items = sorted(kwargs.items())
        key_parts = [prefix] + [f"{k}:{v}" for k, v in sorted_items]
        key_str = ":".join(str(p) for p in key_parts)

        # 긴 키는 해시 처리
        if len(key_str) > 200:
            hash_suffix = hashlib.md5(key_str.encode()).hexdigest()[:16]
            return f"{prefix}:{hash_suffix}"

        return key_str
```

**성능 개선**:
- 캐시 히트: ~10ms (Redis 조회)
- 캐시 미스: ~500ms (MCP 호출)
- 히트율: 60-70% (반복 질문 많은 사용자)

---

### 4. MCP 안정화

**개요**: 공식 MCP Python SDK 사용, 매 호출마다 세션 생성/종료로 Context 문제 완전 해결.

**이전 문제**:
```python
# 문제: 서버 프로세스를 계속 유지하면서 재사용
# → Context 불일치, "handler is closed" 에러
```

**해결 방법** (`mcp_client.py`):

```python
async def call_tool(self, server_name, tool_name, arguments, timeout=5.0):
    """
    매번 세션 생성/종료
    1. Context가 같은 함수에서 생성/종료됨 ✅
    2. Task 불일치 문제 없음 ✅
    3. MCP 표준 완전 준수 ✅
    """
    params = self.server_params.get(server_name)

    # 서버별 직렬화 (프로세스 스폰 경합 방지)
    lock = self._locks[server_name]
    async with lock:
        # stdio_client context: 프로세스 생성/종료
        async with stdio_client(params) as (read, write):
            # ClientSession context: 세션 초기화/종료
            async with ClientSession(read, write) as session:
                # 초기화
                await asyncio.wait_for(session.initialize(), timeout=max(timeout, 12.0))

                # Tool 호출
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments),
                    timeout=max(timeout, 10.0)
                )

                return self._parse_result(result)
    # 여기서 context 자동 종료 ✅
```

**장점**:
- Context 안정성: 100%
- 에러율: ~15% → ~2%
- 디버깅 용이: 각 호출이 독립적

**트레이드오프**:
- 프로세스 생성 오버헤드: ~100ms
- 메모리 효율: 좋음 (프로세스 즉시 종료)

---

### 5. Agent Loop 최적화

**개요**: 최대 반복 횟수를 5회→2회로 줄여 효율성 향상, 순차 Tool 호출로 안정성 확보.

**변경 사항** (`agent_loop.py`):

```python
# 이전: max_iterations = 5
# 현재: max_iterations = 2

max_iterations = 2  # 대부분의 질문은 1-2회로 해결 가능

# 순차 Tool 호출 (MCP stdio 안정성)
tool_calls = []
for content in response.content:
    if content.type == "tool_use":
        tool_calls.append(content)

# 순차 실행
results = []
for tool in tool_calls:
    result = await process_tool_call(...)
    results.append(result)
    await asyncio.sleep(0.1)  # 짧은 대기
```

**근거**:
- 벤치마크 결과: 평균 1.3회 반복
- 3회 이상: 불필요한 Tool 재호출 (오류)
- 순차 실행: stdio 충돌 방지

**성능 영향**:
- 평균 응답시간: 16.6s → 12.5s (**-25%**)
- 성공률: 동일 유지

---

## 📊 성능 벤치마크 (2025-12-17)

### E2E 응답시간

| 질문 유형 | 이전 | 현재 | 개선율 |
|----------|------|------|--------|
| 간단한 QA | 7.8s | 1.0s | **-87%** |
| 학식/장학금 | 9.6s | 6.0s | -38% |
| 공지사항 | 12.6s | 9.0s | -29% |
| 강의실 | 16.1s | 10.0s | -38% |
| 복합/추천 | 23.1s | 12.0s | -48% |
| 교과과정 | 27.9s | 15.0s | -46% |

### 라우팅 분포

```
Total Queries: 1000
├─ Simple (60%)
│  ├─ SLM Success (80%): 480 queries (평균 1.0s)
│  └─ LLM Fallback (20%): 120 queries (평균 6.0s)
└─ Complex (40%): 400 queries (평균 12.0s)

Overall Average: 5.5s (기존 16.6s 대비 -67%)
```

---

## 🔧 시스템 구성 업데이트

### 백엔드 아키텍처

```
backend/app/
├── main.py                   # Lifespan, CORS, 라우터 등록
├── agent/
│   ├── agent_loop.py         # Hybrid LLM/SLM 메인 루프
│   ├── tool_executor.py      # Tool 실행 및 결과 누적
│   ├── tools_definition.py   # Tool 스키마 + 캐시 TTL
│   └── utils.py              # Curriculum intent 감지
├── mcp_client.py             # 공식 MCP SDK 사용
├── cache.py                  # Redis 캐시 매니저
├── observability.py          # Elasticsearch 로깅
├── question_classifier.py    # 질문 분류기
├── slm_agent.py              # SLM Agent (선택)
└── scheduler.py              # 백그라운드 스케줄러
```

### 환경변수

```bash
# 기존
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-...

# 추가
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200
```

### Docker Compose

```yaml
services:
  postgres:    # 데이터베이스
  redis:       # 캐싱 (NEW)
  elasticsearch:  # 로깅 (NEW)
  backend:     # FastAPI
  frontend:    # React
```

---

## 🎯 향후 계획

### 단기 (1주)
- [ ] MCP 병렬 호출 (asyncio.gather)
- [ ] SLM 신뢰도 임계값 A/B 테스팅
- [ ] Notice MCP 크롤링 최적화

### 중기 (1개월)
- [ ] SLM Fine-tuning (Observability 데이터 활용)
- [ ] 캐시 워밍업 자동화
- [ ] 메트릭 대시보드 (Grafana)

### 장기 (3개월)
- [ ] Multi-Modal Agent (이미지, 음성)
- [ ] 개인화된 프롬프트 생성
- [ ] Federation Learning (학습 데이터 공유)

---

## 📚 참고 자료

- [E2E Performance Analysis](../E2E_PERFORMANCE_ANALYSIS.md)
- [Hybrid LLM/SLM Status](../HYBRID_LLM_SLM_STATUS.md)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Elasticsearch Logging](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
