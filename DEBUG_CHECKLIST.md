# 🔍 사용자 인증 문제 디버깅 체크리스트

## 1️⃣ 로그인 상태 확인 (프론트엔드)

브라우저 개발자 도구를 열고 Console에서 확인:

```javascript
// 토큰 확인
localStorage.getItem('token')

// 사용자 정보 확인
localStorage.getItem('user')
```

**결과 해석:**
- ✅ 둘 다 값이 있음 → 로그인 되어있음, 백엔드 문제
- ❌ 둘 다 `null` → **로그인 안 됨! 로그인 페이지로 이동해서 로그인하세요**

---

## 2️⃣ 로그인이 되어있다면 - 토큰 전송 확인

브라우저 개발자 도구 → Network 탭 → "내 학과와 학번을 대답해봐" 입력 후:

1. `chat` 요청 찾기
2. Request Headers 확인
3. `Authorization: Bearer eyJ...` 헤더가 있는지 확인

**결과 해석:**
- ✅ Authorization 헤더 있음 → 백엔드에서 토큰 검증 실패
- ❌ Authorization 헤더 없음 → 프론트엔드 코드 문제

---

## 3️⃣ 백엔드 로그 확인

터미널에서 실시간 로그 확인:

```bash
cd /Users/jung-yoonsuh/Desktop/agent-khu
docker compose logs backend --tail 20 --follow
```

"내 학과와 학번을 대답해봐" 메시지 전송 후 나타나는 로그:

**Case A: 토큰이 아예 없음**
```
🔍 DEBUG [get_current_user_optional] - token: None...
⚠️ DEBUG - 토큰이 없습니다 (비로그인 상태)
🔍 DEBUG - 로그인 안됨 (current_user is None)
```
→ **해결방법**: 로그인하세요!

**Case B: 토큰 검증 실패**
```
🔍 DEBUG [get_current_user_optional] - token: eyJ...
❌ DEBUG - 토큰 검증 실패: Invalid authentication credentials
```
→ **해결방법**: 토큰 만료 또는 잘못됨, 다시 로그인하세요

**Case C: 정상 작동**
```
🔍 DEBUG [get_current_user_optional] - token: eyJ...
✅ DEBUG - 사용자 인증 성공: 2021123456 (홍길동)
🎓 현재 대화 중인 학생 정보:
- 학번: 2021학번
...
```
→ 정상! 사용자 정보를 인식하고 있음

---

## 4️⃣ 빠른 해결 방법

### 로그인이 안 되어있다면:

1. 브라우저에서 `http://localhost:5173/login` 접속
2. 회원가입 또는 로그인
3. 채팅 페이지로 이동
4. 다시 "내 학과와 학번을 대답해봐" 입력

### 로그인은 되어있는데 인식 안 된다면:

**프론트엔드 문제 (토큰 헤더 미전송):**
```typescript
// frontend/src/api/chat.ts 확인
const token = localStorage.getItem('token');
console.log('🔍 Token:', token);  // 디버그 로그 추가

const response = await fetch(`${API_BASE_URL}/chat`, {
    headers: {
        'Authorization': `Bearer ${token}`,  // 이 헤더가 제대로 전송되는지 확인
    },
    ...
});
```

**백엔드 문제 (토큰 파싱 실패):**
- JWT_SECRET_KEY 환경변수 확인
- 토큰 만료 시간 확인
- 다시 로그인해서 새 토큰 발급

---

## 5️⃣ 현재 가장 가능성 높은 원인

스크린샷을 보면:
```
안녕하세요! 저는 현재 로그인되지 않은 상태라서 회원님의 학과와 학번 정보에 접근할 수 없습니다.
```

이 메시지는 `backend/app/agent/utils.py`의 `build_system_prompt()`에서 `current_user`가 `None`일 때 나오는 메시지입니다.

**가장 가능성 높은 원인**: 🎯 **로그인을 안 하셨습니다!**

**즉시 확인**: 브라우저 Console에서 `localStorage.getItem('token')` 입력해보세요.
- `null` 나오면 → 로그인 안 됨
- 문자열 나오면 → 백엔드 토큰 검증 문제

