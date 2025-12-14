"""
유틸리티 함수
"""


def detect_curriculum_intent(message: str) -> dict:
    """메시지에서 교과과정 관련 의도 감지"""
    msg_lower = message.lower()
    
    if any(kw in msg_lower for kw in ["졸업", "요건", "조건", "학점", "이수"]):
        if any(kw in msg_lower for kw in ["현황", "평가", "진행", "확인", "충족"]):
            return {"intent": "progress", "keywords": ["progress", "evaluate"]}
        return {"intent": "requirements", "keywords": ["requirements", "졸업요건"]}
    
    if any(kw in msg_lower for kw in ["학기", "개설", "몇학기"]):
        return {"intent": "semester", "keywords": ["semester", "개설"]}
    
    if any(kw in msg_lower for kw in ["과목", "수업", "강의", "코드"]):
        return {"intent": "course_search", "keywords": ["search", "과목"]}
    
    return {"intent": None}


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
- 학번: {current_user.student_id[:4]}학번 (입학년도: {current_user.admission_year})
- 학과: {current_user.department}
- 캠퍼스: {current_user.campus}
- 학년: {grade_str}
- 이수 학점: {current_user.completed_credits or 0}/130학점
- 관심 분야: {interests_str}

📋 중요한 지침:
1. 학생의 학번({current_user.admission_year}학번)과 학과({current_user.department})에 맞는 졸업 요건을 제공하세요
2. 학생의 캠퍼스({current_user.campus})에 맞는 정보(건물, 셔틀, 식당)를 제공하세요
3. 이수 학점({current_user.completed_credits or 0}학점)을 고려하여 답변하세요
4. 학생의 관심 분야({interests_str})와 관련된 추천을 우선하세요
5. 친근하게 대화하되 존댓말을 사용하세요

학생에게 가장 도움이 되는 정보를 제공하세요."""
    else:
        return """당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

💡 로그인하시면 학번에 맞는 졸업요건, 수강 추천 등 맞춤형 정보를 제공받으실 수 있습니다.""" + hint_text
