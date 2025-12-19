"""
유틸리티 함수
"""


def detect_curriculum_intent(message: str) -> dict:
    """메시지에서 교과과정 관련 의도 감지 + 연도 추출"""
    msg_lower = message.lower()

    # 연도 패턴 추출 (예: 2019, 2025, 19학번, 25년)
    import re
    year = None
    # 4자리 숫자 우선
    m = re.search(r"(20\d{2})", message)
    if m:
        year = m.group(1)
    else:
        # 2자리 + '년' or '학번'
        m2 = re.search(r"(\d{2})\s*(?:년|학번)", message)
        if m2:
            y2 = int(m2.group(1))
            # 2015~2029 범위로 맵핑
            year = f"20{y2:02d}"

    if any(kw in msg_lower for kw in ["졸업", "요건", "조건", "학점", "이수"]):
        if any(kw in msg_lower for kw in ["현황", "평가", "진행", "확인", "충족"]):
            return {"intent": "progress", "keywords": ["progress", "evaluate"], "year": year}
        return {"intent": "requirements", "keywords": ["requirements", "졸업요건"], "year": year}

    if any(kw in msg_lower for kw in ["학기", "개설", "몇학기"]):
        return {"intent": "semester", "keywords": ["semester", "개설"], "year": year}

    if any(kw in msg_lower for kw in ["과목", "수업", "강의", "코드"]):
        return {"intent": "course_search", "keywords": ["search", "과목"], "year": year}

    return {"intent": None, "year": year}


def build_system_prompt(current_user, hint_text: str = "") -> str:
    """
    사용자 프로필 기반 system prompt 생성
    
    로그인 사용자: 학과, 입학년도, 이수학점 기반 자동 처리
    미로그인: 기본 설정
    """
    if current_user:
        return f"""경희대학교 AI 어시스턴트입니다.

[사용자 정보 (자동 적용)]
- 학번: {current_user.student_id}
- 입학년도: {current_user.admission_year}년
- 학과: {current_user.department}
- 캠퍼스: {current_user.campus}
- 이수 학점: {current_user.completed_credits or 0}/130학점

[사용 가능 도구]
✓ get_requirements: 사용자의 입학년도/학과 기준 졸업요건 자동 조회
✓ evaluate_progress: 사용자의 졸업 진행도 자동 평가
✓ search_classroom, search_notices, get_seat_availability, etc.

[처리 규칙]
1. "졸업요건" 관련 질문 → 즉시 get_requirements() 호출 (program, year 자동 적용)
2. "진행도/평가" 질문 → 즉시 evaluate_progress() 호출 (program, year 자동 적용)
3. 사용자가 program/year를 명시하면 그 값 우선 사용
4. 이미 알고 있는 정보(학번, 학과, 학점)는 다시 묻지 말 것
5. 응답: 친근하고 정확하게, 자신 있게 정보 제시

[예시]
- 사용자: "졸업요건을 알려줄래?" 
  → 자동: get_requirements() 호출 (2021년도 컴퓨터공학과 기준)
  
- 사용자: "졸업까지 몇 학점 남았어?"
  → 자동: evaluate_progress() 호출 (2021년도 기준, 현재 이수학점 적용){hint_text}"""
    else:
        return f"""경희대학교 AI 어시스턴트입니다.

[미로그인 상태]
사용자 정보가 없습니다. 필요시 안내해주세요.

[사용 가능 도구]
✓ get_requirements: 졸업요건 조회 (program, year 필수 명시)
✓ evaluate_progress: 진행도 평가
✓ search_classroom, search_notices, get_seat_availability, etc.

[처리 규칙]
1. 로그인하지 않았다면 학과/학번을 물어본 후 처리
2. 도구 호출 시 program, year 명시 필요
3. 간결하고 친근하게 응답{hint_text}"""