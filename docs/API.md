# API 문서 📡

Agent KHU Backend REST API 엔드포인트 문서입니다.

---

## 📋 목차

- [인증](#인증)
- [채팅](#채팅)
- [프로필](#프로필)
- [강의실](#강의실)
- [공지사항](#공지사항)
- [에러 코드](#에러-코드)

---

## 기본 정보

**Base URL**: `http://localhost:8000`

**Content-Type**: `application/json`

**인증 방식**: JWT Bearer Token

---

## 인증

### 회원가입

**POST** `/api/auth/register`

학번으로 회원가입합니다.

**Request Body**
```json
{
  "student_id": "2019104488",
  "password": "your_password",
  "name": "정윤서",
  "department": "컴퓨터공학과",
  "admission_year": 2019,
  "campus": "서울"
}
```

**Response** `201 Created`
```json
{
  "student_id": "2019104488",
  "name": "정윤서",
  "department": "컴퓨터공학과",
  "email": "example@khu.ac.kr"
}
```

**Error** `400 Bad Request`
```json
{
  "detail": "이미 등록된 학번입니다"
}
```

---

### 로그인

**POST** `/api/auth/login`

JWT 토큰을 발급받습니다.

**Request Body**
```json
{
  "student_id": "2019104488",
  "password": "your_password"
}
```

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "student_id": "2019104488",
    "name": "정윤서",
    "department": "컴퓨터공학과"
  }
}
```

**Error** `401 Unauthorized`
```json
{
  "detail": "학번 또는 비밀번호가 올바르지 않습니다"
}
```

---

## 채팅

### 메시지 전송

**POST** `/api/chat`

Claude AI와 대화합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Request Body**
```json
{
  "message": "자료구조는 몇 학점이야?",
  "user_latitude": 37.5665,
  "user_longitude": 127.0000
}
```

**Response** `200 OK`
```json
{
  "response": "자료구조는 3학점 전공 필수 과목입니다. 1학기와 2학기 모두 수강 가능합니다.",
  "tool_calls": [
    {
      "tool": "search_courses",
      "args": {"query": "자료구조"}
    }
  ],
  "map_data": null,
  "notice_data": null,
  "course_data": null
}
```

**Response Fields**
- `response` (string): AI 응답 텍스트
- `tool_calls` (array): 사용된 Tool 목록
- `map_data` (object|null): 지도 데이터 (강의실 검색 시)
- `notice_data` (array|null): 공지사항 목록
- `course_data` (array|null): 수강신청 과목 목록

**Error** `401 Unauthorized`
```json
{
  "detail": "인증이 필요합니다"
}
```

---

## 프로필

### 프로필 조회

**GET** `/api/profiles/me`

현재 사용자 프로필을 조회합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Response** `200 OK`
```json
{
  "student_id": "2019104488",
  "name": "정윤서",
  "department": "컴퓨터공학과",
  "admission_year": 2019,
  "campus": "서울",
  "completed_credits": 85,
  "interests": ["AI", "백엔드"]
}
```

---

### 프로필 수정

**PUT** `/api/profiles/me`

프로필 정보를 수정합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Request Body**
```json
{
  "completed_credits": 90,
  "interests": ["AI", "백엔드", "MCP"]
}
```

**Response** `200 OK`
```json
{
  "student_id": "2019104488",
  "completed_credits": 90,
  "interests": ["AI", "백엔드", "MCP"]
}
```

---

## 강의실

### 강의실 검색

**GET** `/api/classrooms/search`

강의실을 검색합니다.

**Query Parameters**
- `query` (string, required): 검색어
- `limit` (integer, optional): 최대 결과 수 (기본값: 5)

**Example**
```
GET /api/classrooms/search?query=전정&limit=10
```

**Response** `200 OK`
```json
{
  "classrooms": [
    {
      "id": 1,
      "name": "전자정보대학관 605호",
      "building": "전자정보대학관",
      "room_number": "605",
      "floor": 6,
      "latitude": 37.2425,
      "longitude": 127.0792,
      "description": "강의실"
    }
  ],
  "count": 1
}
```

---

### 강의실 상세 조회

**GET** `/api/classrooms/{classroom_id}`

특정 강의실의 상세 정보를 조회합니다.

**Response** `200 OK`
```json
{
  "id": 1,
  "name": "전자정보대학관 605호",
  "building": "전자정보대학관",
  "room_number": "605",
  "floor": 6,
  "latitude": 37.2425,
  "longitude": 127.0792,
  "description": "강의실"
}
```

**Error** `404 Not Found`
```json
{
  "detail": "강의실을 찾을 수 없습니다"
}
```

---

## 공지사항

### 공지사항 검색

**GET** `/api/notices/search`

공지사항을 검색합니다.

**Query Parameters**
- `query` (string, required): 검색어
- `limit` (integer, optional): 최대 결과 수 (기본값: 10)

**Example**
```
GET /api/notices/search?query=수강신청&limit=5
```

**Response** `200 OK`
```json
{
  "notices": [
    {
      "id": 1,
      "title": "2025학년도 1학기 수강신청 안내",
      "content": "수강신청 일정을 안내드립니다...",
      "url": "https://ce.khu.ac.kr/notice/1234",
      "date": "2024-12-01",
      "category": "학사"
    }
  ],
  "count": 1
}
```

---

### 최신 공지사항 조회

**GET** `/api/notices/latest`

최신 공지사항을 조회합니다.

**Query Parameters**
- `limit` (integer, optional): 최대 결과 수 (기본값: 10)

**Example**
```
GET /api/notices/latest?limit=5
```

**Response** `200 OK`
```json
{
  "notices": [
    {
      "id": 1,
      "title": "2025학년도 1학기 수강신청 안내",
      "date": "2024-12-01"
    }
  ],
  "count": 5
}
```

---

## 에러 코드

### HTTP Status Codes

| Code | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 500 | Internal Server Error | 서버 오류 |

### Error Response Format

```json
{
  "detail": "에러 메시지"
}
```

---

## 인증 방법

### JWT 토큰 사용

1. **로그인**하여 토큰 발급
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id":"2019104488","password":"your_password"}'
```

2. **Authorization Header**에 토큰 추가
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"message":"자료구조는 몇 학점이야?"}'
```

### 토큰 만료

- **만료 시간**: 1시간 (기본값)
- **만료 후**: 재로그인 필요
- **연장**: 현재 미지원 (향후 Refresh Token 추가 예정)

---

## 예제 코드

### Python (requests)

```python
import requests

# 로그인
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"student_id": "2019104488", "password": "your_password"}
)
token = response.json()["access_token"]

# 채팅
response = requests.post(
    "http://localhost:8000/api/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={"message": "자료구조는 몇 학점이야?"}
)
print(response.json()["response"])
```

### JavaScript (fetch)

```javascript
// 로그인
const loginResponse = await fetch("http://localhost:8000/api/auth/login", {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    student_id: "2019104488",
    password: "your_password"
  })
});
const { access_token } = await loginResponse.json();

// 채팅
const chatResponse = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${access_token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: "자료구조는 몇 학점이야?"
  })
});
const data = await chatResponse.json();
console.log(data.response);
```

### cURL

```bash
# 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id":"2019104488","password":"your_password"}' \
  | jq -r '.access_token')

# 채팅
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"자료구조는 몇 학점이야?"}'
```

---

## Swagger UI

FastAPI 자동 생성 API 문서:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 참고

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [JWT 소개](https://jwt.io/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)