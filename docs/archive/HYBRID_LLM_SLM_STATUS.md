# Agent KHU Hybrid LLM/SLM 시스템 - 현황 보고서

**최종 업데이트**: 2025년 12월 14일 22:30 KST

## 📋 작업 진행 상황

| 단계 | 작업 | 상태 | 파일 |
|------|------|------|------|
| 1️⃣ | 데이터셋 확장 (40→150개) | ✅ 완료 | `backend/scripts/questions.txt` |
| 2️⃣ | 데이터 수집 | 🔄 진행 중 | `backend/scripts/collect_data.py` |
| 3️⃣ | 학습 데이터 추출 | ⏳ 대기 | `backend/scripts/extract_training_data.py` |
| 4️⃣ | 모델 파인튜닝 | ⏳ 대기 | `backend/scripts/finetune_slm.py` |
| 5️⃣ | **SLM Agent 구현** | ✅ 완료 | `backend/app/slm_agent.py` |
| 6️⃣ | **라우터 로직** | ✅ 완료 | `backend/app/agent/agent_loop.py` |
| 7️⃣ | 통합 테스트 | ⏳ 대기 | - |

## ✨ 완료된 핵심 기능

### 1. SLM Agent 구현 (`backend/app/slm_agent.py`)

```python
class SLMAgent:
    ✅ 모델 자동 탐색
       - models/finetuned/ 디렉토리에서 최신 모델 자동 검색
       - 모델이 없으면 graceful degradation
    
    ✅ 조건부 로드
       - GPU 사용 가능 시 GPU, 아니면 CPU 사용
       - torch 미설치 시 LLM으로 fallback
    
    ✅ 비동기 생성
       - async def generate() 지원
       - max_new_tokens, temperature 조절 가능
    
    ✅ 품질 평가
       - 신뢰도 점수 (0.0 ~ 1.0)
       - 너무 짧은 답변, 실패 표현, hallucination 감지
    
    ✅ Fallback 메커니즘
       - 신뢰도 < 0.7이면 자동으로 LLM 호출
```

### 2. 라우터 로직 구현 (`backend/app/agent/agent_loop.py`)

```
사용자 질문
    ↓
질문 분류기
├─ Simple (단순 정보 검색)
│   ├→ SLM 시도 (Bllossom-8B)
│   │   ├→ 신뢰도 >= 0.7? → ✅ SLM 응답 반환
│   │   └→ 신뢰도 < 0.7? → LLM Fallback ↓
│   
└─ Complex (다단계 추론)
    └→ LLM 사용 (Claude Sonnet 4)
        └→ 응답 반환

모든 요청 → Elasticsearch 로깅
  - routing_decision: "slm" | "llm" | "llm_fallback"
  - question_type: "simple" | "complex"
  - 응답 시간, 성공 여부 등
```

## 🔄 현재 진행 중인 작업

### 데이터 수집 (2단계)

```bash
프로세스: python3 backend/scripts/collect_data.py
상태: 백그라운드 실행 중
로그: /Users/jung-yoonsuh/Desktop/agent-khu/backend/scripts/collect_final.log

진행 상황:
- 150개 질문을 자동으로 API 호출
- 각 응답을 Elasticsearch에 저장
- 예상 완료: 20-25분 (총 시간 기준)
```

## 🎯 다음 단계 (자동 실행 순서)

### 3단계: 학습 데이터 추출 (2-3분)
데이터 수집 완료 후:
```bash
cd backend/scripts
python3 extract_training_data.py
# → training_data.jsonl 생성 (100+ 샘플)
```

### 4단계: 모델 파인튜닝 (1-2시간, GPU 권장)
```bash
cd backend/scripts
python3 finetune_slm.py
# → models/finetuned/bllossom-khu-YYYYMMDD_HHMMSS/ 생성
```

이후 SLM Agent가 자동으로 모델을 로드합니다.

### 7단계: 시스템 테스트
```bash
# Simple 질문 (SLM으로 처리 예정)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "자료구조 몇 학점?"}' \
  --max-time 5

# Complex 질문 (LLM으로 처리)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "좋은 전공선택 과목들 추천해줘"}' \
  --max-time 30
```

## 💾 데이터셋 확장 상세

### questions.txt (40 → 150개)

**강의실 위치 (10개)**
- 전101 어디야
- 전203은 어디에 있어?
- 전자정보대학관 몇 층까지 있어?
- ... 외 7개

**과목 정보 (25개)**
- 알고리즘 몇 학점?
- 자료구조 언제 개설돼?
- 딥러닝 과목 있어?
- ... 외 22개

**학식 메뉴 (10개)**
- 오늘 학식 메뉴 뭐야?
- 내일 아침 메뉴
- 이번주 수요일 학식
- ... 외 7개

**도서관 시설 (10개)**
- 도서관 몇 시까지 해?
- 열람실 좌석 있어?
- 1열람실 자리 있어?
- ... 외 7개

**공지사항 (15개)**
- SW융합대학 공지사항
- 수강신청 공지 있어?
- 장학금 공지 알려줘
- ... 외 12개

**셔틀버스 (10개)**
- 셔틀버스 시간표
- 다음 셔틀 언제 와?
- 아침 첫 셔틀 시간
- ... 외 7개

**졸업요건 (20개)**
- 졸업요건 알려줘
- 전공필수 몇 학점?
- 교양 학점 몇 개 들어야 해?
- ... 외 17개

**수강신청 (20개)**
- 수강신청 기간 언제야?
- 수강신청 정정 기간
- 수강철회 가능해?
- ... 외 17개

**학사관련 (20개)**
- 휴학 신청 방법
- 복학 신청 기간
- 자퇴 절차 알려줘
- ... 외 17개

## 📊 시스템 아키텍처

```
┌──────────────────────────────────────────────────┐
│          사용자 (학생)                             │
└─────────────────┬────────────────────────────────┘
                  │ HTTPS
        ┌─────────▼─────────┐
        │  React Frontend   │
        │  (Vite)          │
        └─────────┬─────────┘
                  │ HTTP/REST
        ┌─────────▼──────────────────────────────┐
        │  FastAPI Backend                       │
        │                                        │
        │  ┌────────────────────────────────┐   │
        │  │ Question Classifier            │   │
        │  │ (Simple/Complex)               │   │
        │  └────────────┬───────────────────┘   │
        │               │                        │
        │      ┌────────┴────────┐              │
        │      │                 │              │
        │      ▼                 ▼              │
        │   ┌────────┐       ┌────────┐       │
        │   │ SLM    │       │ LLM    │       │
        │   │Agent   │       │(Claude)│       │
        │   │        │       │        │       │
        │   │Bllossom│       │Sonnet4│       │
        │   └────────┘       └────────┘       │
        │                                      │
        │  ┌───────────────────────────────┐  │
        │  │  Observability Logger         │  │
        │  │  (question_type, routing...)  │  │
        │  └───────────────┬───────────────┘  │
        └────────────────┼──────────────────────┘
                         │ JSON
        ┌────────────────▼────────────────┐
        │  Elasticsearch                  │
        │  (agent-khu-interactions index) │
        │                                 │
        │  - routing_decision: "slm"|"llm"│
        │  - question_type: "simple"|...  │
        │  - latency_ms                   │
        │  - success: true/false          │
        └─────────────────────────────────┘
```

## 💰 비용 절감 분석

### 현재 상태 (모두 Claude 사용)
```
월 1000개 질문 × $0.006/질문 = $6/월
```

### Hybrid 적용 후
```
Simple 질문: 600개 × 60% = 360개
  └─ SLM 처리: 360개 × 80% (신뢰도 >= 0.7) = 288개
     → 비용: $0.02 (자체 호스팅)
  
  └─ LLM Fallback: 360개 × 20% = 72개
     → 비용: $0.43

Complex 질문: 400개
  └─ LLM 처리 (필수)
     → 비용: $2.40

총 월 비용: $2.85
절감액: $3.15/월 (52.5% 절감) 💰
```

**연간 절감액: $37.80** 🎉

## 🚀 시스템 체크리스트

- ✅ 질문 분류기 (question_classifier.py)
- ✅ Observability Logger (observability.py)
- ✅ SLM Agent (slm_agent.py) - **NEW**
- ✅ 라우터 로직 (agent_loop.py) - **UPDATED**
- ✅ 데이터 수집 스크립트 (collect_data.py)
- ⏳ 학습 데이터 (training_data.jsonl) - 수집 완료 후
- ⏳ 파인튜닝된 모델 (models/finetuned/) - 학습 완료 후
- 📊 시스템 모니터링

## 🔧 주요 설정값

```python
# question_classifier.py
SIMPLE_PATTERNS = [
  r"몇\s*학점",    # Simple
  r"어디",
  r"위치",
  r"언제",
  ...
]

COMPLEX_PATTERNS = [
  r"추천",        # Complex
  r"어떤\s*것",
  r"비교",
  r"분석",
  ...
]

# slm_agent.py
CONFIDENCE_THRESHOLD = 0.7  # SLM 신뢰도 임계값

# agent_loop.py
routing_decision in ["slm", "llm", "llm_fallback"]
```

## 📝 기술 스택

| 계층 | 기술 |
|------|------|
| **Frontend** | React 18 + TypeScript + Vite + TailwindCSS |
| **Backend** | FastAPI + SQLAlchemy + JWT |
| **LLM** | Claude Sonnet 4 (Anthropic) |
| **SLM** | Bllossom-8B (한국어) with LoRA |
| **분류기** | 정규식 기반 heuristic |
| **Observability** | Elasticsearch 8.11 |
| **Cache** | Redis 7 |
| **DB** | PostgreSQL 15 |
| **Infrastructure** | Docker Compose |

## ✨ 완성도

```
┌─────────────────────────────────────────┐
│         시스템 완성도 분석               │
├─────────────────────────────────────────┤
│ 분류기 & Observability    [████████] 100% │
│ 라우터 로직              [████████] 100% │
│ SLM Agent 구현           [████████] 100% │
│ 데이터 수집              [██████  ] 75%  │
│ 모델 파인튜닝            [        ] 0%   │
│ 통합 테스트              [        ] 0%   │
├─────────────────────────────────────────┤
│ 전체 진행률              [██████  ] 63%  │
└─────────────────────────────────────────┘
```

## 🎓 학습 및 개선 사항

이 프로젝트를 통해 구현된 패턴:

1. **Hybrid AI 아키텍처**: LLM과 SLM 조합으로 비용 최적화
2. **Observable System**: 모든 상호작용을 로깅하여 데이터 기반 최적화
3. **Graceful Degradation**: 모델 없어도 LLM으로 자동 대체
4. **Async-first Design**: 빠른 응답 시간을 위한 비동기 처리
5. **Scalable Data Pipeline**: 자동 데이터 수집 → 학습 파이프라인

## 📞 다음 액션 아이템

1. **데이터 수집 모니터링** (진행 중)
   ```bash
   watch 'wc -l /path/to/collect_final.log'
   ```

2. **완료 후 자동 실행**
   ```bash
   cd backend/scripts && python3 extract_training_data.py
   python3 finetune_slm.py
   ```

3. **모델 로드 확인**
   - 백엔드 로그에서 "✅ SLM 모델 로드 성공" 확인
   - SLM Agent가 자동으로 최신 모델 로드

4. **시스템 테스트**
   - Simple/Complex 질문 구분 확인
   - 라우팅 결정 (routing_decision) 확인
   - 응답 시간 및 신뢰도 측정

---

**문의 사항 및 추가 개선 사항은 프로젝트 README.md를 참고하세요.**
