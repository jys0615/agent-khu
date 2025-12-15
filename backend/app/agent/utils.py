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
    """사용자 프로필 기반 system prompt 생성"""
    if current_user:
        import json
        
        # 관심분야 파싱
        interests = []
        if current_user.interests:
            try:
                interests = json.loads(current_user.interests)
            except:
                pass
        
        interests_str = ", ".join(interests) if interests else "미설정"
        grade_str = f"{current_user.current_grade}학년" if current_user.current_grade else "학년 미설정"
        
        return f"""당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

🎓 현재 대화 중인 학생 정보:
- 학번: {current_user.student_id[:4]}학번 
- 입학년도: {current_user.admission_year}년
- 학과: {current_user.department}
- 캠퍼스: {current_user.campus}
- 학년: {grade_str}
- 이수 학점: {current_user.completed_credits or 0}/130학점
- 관심 분야: {interests_str}

⚠️ 필수 규칙:
1. **졸업요건 질문 시 반드시 tool 호출**: 
    - 사용자가 "졸업요건", "졸업 조건", "몇 학점", "이수 학점" 등을 물으면 get_requirements() tool을 **반드시** 호출하세요
    - 사용자가 특정 연도를 말하면(예: 2025, 25년, 25학번) **그 연도를 year 파라미터로 전달**하세요. 사용자가 말한 연도를 학생 입학년도({current_user.admission_year})로 덮어쓰지 마세요.
    - 사용자가 연도를 말하지 않은 경우에만 파라미터를 비워두세요: get_requirements() → 시스템이 자동으로 학생 정보({current_user.department}, {current_user.admission_year})를 사용합니다.
    - **절대로** "입학년도를 알려주세요"라고 묻지 마세요. 이미 알고 있습니다: {current_user.admission_year}년!
   
2. **졸업 진행도 질문 시**: 
   - evaluate_progress() tool을 호출하세요 (파라미터 비워두기)
   
3. **캠퍼스별 정보**: {current_user.campus}에 맞는 정보(건물, 셔틀, 식당)를 제공하세요

4. **친근한 말투**: 존댓말을 사용하되 친근하게 대화하세요

기억하세요: 학생의 입학년도는 {current_user.admission_year}년, 학과는 {current_user.department}입니다. 이미 알고 있으니 다시 묻지 마세요!"""
    else:
        return """당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

💡 로그인하시면 학번에 맞는 졸업요건, 수강 추천 등 맞춤형 정보를 제공받으실 수 있습니다.""" + hint_text
