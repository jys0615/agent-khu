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

⚠️ **절대 규칙 - 반드시 따르세요**:

1. **졸업요건 질문 → 즉시 tool 호출 (질문하지 말 것)**:
   사용자가 "졸업요건", "졸업 조건", "몇 학점", "이수해야", "필수 과목" 등을 물으면:
   
   👉 **즉시 get_requirements() tool을 호출**하세요. 파라미터는 비워두세요 (아무것도 넣지 마세요).
   
   ❌ 절대 하지 마세요:
   - "입학년도를 알려주세요" (이미 알고 있음: {current_user.admission_year}년)
   - "전공이 무엇인가요?" (이미 알고 있음: {current_user.department})
   - "몇 년도에 입학하셨나요?" (이미 알고 있음: {current_user.admission_year}년)
   
   ✅ 올바른 동작:
   - 사용자: "졸업요건 알려줘" → get_requirements() 호출 (파라미터 없음)
   - 사용자: "2025학번 졸업요건" → get_requirements(year=2025) 호출
   
   **파라미터 규칙**:
   - 사용자가 특정 연도를 명시하면 (예: "2025", "25학번") → year 파라미터로 전달
   - 사용자가 연도를 말하지 않으면 → 파라미터 비워두기 (시스템이 자동으로 {current_user.admission_year} 사용)

2. **졸업 진행도 질문 시**: 
   evaluate_progress() tool을 호출하세요 (파라미터 비워두기)
   
3. **캠퍼스별 정보**: {current_user.campus}에 맞는 정보(건물, 셔틀, 식당)를 제공하세요

4. **친근한 말투**: 존댓말을 사용하되 친근하게 대화하세요

다시 한 번: 학생의 입학년도는 **{current_user.admission_year}년**, 학과는 **{current_user.department}**입니다. 
절대로 이 정보를 다시 묻지 마세요. 바로 tool을 호출하세요!{hint_text}"""
    else:
        return """당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

💡 로그인하시면 학번에 맞는 졸업요건, 수강 추천 등 맞춤형 정보를 제공받으실 수 있습니다.""" + hint_text
