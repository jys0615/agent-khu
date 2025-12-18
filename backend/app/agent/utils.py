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
    """사용자 프로필 기반 system prompt 생성 (간결화)"""
    if current_user:
        return f"""경희대학교 AI 어시스턴트입니다.

학생 정보:
- {current_user.admission_year}학번, {current_user.department}, {current_user.campus}
- 이수: {current_user.completed_credits or 0}/130학점

도구:
- 학식/도서관/공지사항/수강신청/졸업요건/강의실

규칙:
1. 졸업요건 질문 → 즉시 get_requirements({current_user.admission_year}) 호출
2. 이미 알고 있는 정보(학번, 학과, 학점)는 다시 묻지 말 것
3. 친근하고 간결하게 답변{hint_text}"""
    else:
        return f"""경희대학교 AI 어시스턴트입니다.

도구: 학식/도서관/공지사항/수강신청/졸업요건/강의실

규칙:
1. 졸업요건 질문 → get_requirements() 즉시 호출
2. 추가 질문 없이 바로 도구 사용
3. 간결하게 답변{hint_text}"""