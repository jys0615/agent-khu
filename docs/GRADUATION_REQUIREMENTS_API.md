# 졸업요건 API 가이드

## 개요

사용자 로그인 정보(학번, 학과, 입학년도)를 기반으로 졸업요건을 자동으로 조회하고 진행도를 평가하는 시스템입니다.

## 아키텍처

```
사용자 로그인 (학번, 학과, 입학년도 저장)
    ↓
프로필 API / Chat API
    ↓
Tool Executor (사용자 정보 자동 추출)
    ↓
MCP Curriculum Server (JSON 데이터 조회)
    ↓
응답 반환 (사용자 정보 + 졸업요건 데이터)
```

## API 엔드포인트

### 1. 프로필 API

#### GET `/api/profiles/me`
**현재 로그인 사용자 프로필 조회**

```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profiles/me
```

**응답:**
```json
{
  "id": 1,
  "student_id": "2021012345",
  "name": "김경희",
  "department": "컴퓨터공학과",
  "campus": "국제캠퍼스",
  "admission_year": 2021,
  "is_transfer": false,
  "completed_credits": 90,
  "current_grade": 3
}
```

#### GET `/api/profiles/graduation-requirements`
**사용자의 졸업요건 조회 (로그인 필수)**

사용자의 학과, 입학년도를 기반으로 자동 조회합니다.

```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profiles/graduation-requirements
```

**응답:**
```json
{
  "student_id": "2021012345",
  "department": "컴퓨터공학과",
  "admission_year": 2021,
  "found": true,
  "requirements": {
    "year": 2021,
    "program": "KHU-CSE",
    "program_name": "컴퓨터공학과",
    "single_major": {
      "total_credits": 130,
      "major_credits": 84,
      "groups": [
        {
          "name": "전공필수",
          "credits": 45,
          "courses": ["CS101", "CS102", ...]
        },
        {
          "name": "전공선택",
          "credits": 39,
          "courses": [...]
        }
      ]
    }
  }
}
```

#### GET `/api/profiles/graduation-progress`
**졸업요건 진행도 평가 (로그인 필수)**

사용자의 이수 학점을 기반으로 남은 학점, 필수 과목 미충족 내역 등을 계산합니다.

```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profiles/graduation-progress
```

**응답:**
```json
{
  "student_id": "2021012345",
  "department": "컴퓨터공학과",
  "admission_year": 2021,
  "completed_credits": 90,
  "found": true,
  "evaluation": {
    "total_required": 130,
    "completed": 90,
    "remaining": 40,
    "progress_percentage": 69.2,
    "status": "진행 중",
    "major_status": {
      "required_satisfied": true,
      "elective_remaining": 15
    }
  }
}
```

#### GET `/api/profiles/graduation-status`
**졸업 요건 통합 현황 (로그인 필수)**

졸업요건 정보와 진행도를 함께 조회합니다.

```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/profiles/graduation-status
```

**응답:**
```json
{
  "student_id": "2021012345",
  "name": "김경희",
  "department": "컴퓨터공학과",
  "admission_year": 2021,
  "completed_credits": 90,
  "requirements": {
    "found": true,
    "data": { /* 졸업요건 데이터 */ }
  },
  "progress": {
    "found": true,
    "data": { /* 진행도 데이터 */ }
  }
}
```

### 2. Chat API

#### POST `/api/chat`
**사용자 질문에 대한 AI 응답**

사용자의 로그인 정보를 자동으로 활용하여 졸업요건 질문에 답변합니다.

```bash
curl -X POST \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"message": "졸업요건을 알려줄래?"}' \
  http://localhost:8000/api/chat
```

**응답:**
```json
{
  "message": "2021년도 컴퓨터공학과 졸업요건은 다음과 같습니다:\n\n📚 총 130학점 필요\n  - 전공필수: 45학점\n  - 전공선택: 39학점\n  - 교양: ...",
  "requirements": { /* 졸업요건 데이터 */ },
  "show_requirements": true
}
```

## 사용자 정보 기반 자동 처리

### get_requirements Tool

**로그인 사용자:**
- `program` (선택): 비워두면 `current_user.department` → 프로그램 코드로 변환
- `year` (선택): 비워두면 `current_user.admission_year` 사용

```python
# 내부 처리
dept_map = {
    "컴퓨터공학과": "KHU-CSE",
    "소프트웨어융합학과": "KHU-SW",
    "전자공학과": "KHU-ECE",
    ...
}

program = dept_map.get(current_user.department, "KHU-CSE")  # 자동
year = str(current_user.admission_year)  # 자동
```

**미로그인 사용자:**
- `program`, `year` 명시 필수

### evaluate_progress Tool

**로그인 사용자:**
- `program` (선택): 자동
- `year` (선택): 자동
- `taken_courses` (선택): 사용자의 `completed_credits` 반영

**미로그인 사용자:**
- 모두 명시 필수

## 학과 코드 매핑

| 학과명 | 프로그램 코드 |
|--------|--------------|
| 컴퓨터공학과 | KHU-CSE |
| 컴퓨터공학부 | KHU-CSE |
| 소프트웨어융합학과 | KHU-SW |
| 인공지능학과 | KHU-AI |
| 전자공학과 | KHU-ECE |
| 산업경영공학과 | KHU-IME |

## 시스템 프롬프트 최적화

로그인 사용자의 경우, Claude AI 에이전트에게 다음 정보가 자동으로 전달됩니다:

```
[사용자 정보 (자동 적용)]
- 학번: 2021012345
- 입학년도: 2021년
- 학과: 컴퓨터공학과
- 캠퍼스: 국제캠퍼스
- 이수 학점: 90/130학점

[처리 규칙]
1. "졸업요건" 관련 질문 → 즉시 get_requirements() 호출 (program, year 자동 적용)
2. "진행도/평가" 질문 → 즉시 evaluate_progress() 호출 (program, year 자동 적용)
```

## 로깅 및 디버깅

### 에이전트 루프 로깅

```
✅ 로그인 사용자:
   └─ 학번: 2021012345
   └─ 입학년도: 2021년
   └─ 학과: 컴퓨터공학과
   └─ 캠퍼스: 국제캠퍼스
   └─ 이수학점: 90/130
   └─ [자동 적용] get_requirements, evaluate_progress 툴에서 사용됨
```

### Tool Executor 로깅

```
✅ 사용자 학과(컴퓨터공학과) → 프로그램(KHU-CSE)
✅ 사용자 입학년도(2021) 적용
📞 MCP call: get_requirements(program=KHU-CSE, year=2021, user=2021012345)
✅ 졸업요건 조회 성공: KHU-CSE 2021학번
💾 Cache SAVE: get_requirements (TTL: 3600s)
```

## 캐싱 전략

| Tool | TTL | 캐시 가능 |
|------|-----|---------|
| get_requirements | 1시간 | ✓ |
| evaluate_progress | 1시간 | ✓ |
| get_seat_availability | - | ✗ (실시간) |
| reserve_seat | - | ✗ (상태변경) |

**캐시 키:** `program` + `year` + `courses_hash`

## 에러 처리

### 졸업요건 조회 실패

```json
{
  "found": false,
  "error": "Curriculum MCP 서버 응답 없음"
}
```

### MCP 서버 타임아웃

```
타임아웃: 10초
재시도: 2회
```

### 학과 미매핑

기본값 적용: `KHU-CSE`

## 확장 가능성

### 새로운 학과 추가

[tool_executor.py](../backend/app/agent/tool_executor.py#L395-L415)의 `dept_map` 업데이트:

```python
dept_map = {
    "컴퓨터공학과": "KHU-CSE",
    "새로운학과": "KHU-NEW",  # ← 추가
    ...
}
```

### 다중전공 지원

향후 `double_major`, `minor` 필드 활용:

```python
# evaluate_progress에서
if current_user.double_major:
    # 다전공 필수과목 추가 검증
```

## 테스트 시나리오

### 1. 단순 졸업요건 조회

```bash
질문: "졸업요건이 뭐야?"
자동 적용: 2021년도 컴퓨터공학과 기준
응답: 졸업요건 정보 반환
```

### 2. 진행도 평가

```bash
질문: "내가 졸업까지 몇 학점 더 필요해?"
자동 적용: 2021년도, 현재 90학점 기반
응답: 남은 40학점 안내
```

### 3. 특정 연도 조회 (명시)

```bash
질문: "2019학번이라면 졸업요건이 뭘까?"
처리: 2019년도 기준으로 조회 (명시값 우선)
```

---

**마지막 업데이트:** 2025-12-19
