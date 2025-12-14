"""
Question Classifier for Agent KHU
질문을 Simple/Complex로 분류하여 적절한 Agent로 라우팅
"""
from typing import Literal
import re

class QuestionClassifier:
    """질문을 Simple/Complex로 분류"""
    
    # Simple: 단순 정보 검색 패턴
    SIMPLE_PATTERNS = [
        r"몇\s*학점",
        r"학점\s*(수|이)",
        r"언제",
        r"시간",
        r"일정",
        r"어디",
        r"위치",
        r"장소",
        r"누구",
        r"교수",
        r"담당",
        r"메뉴",
        r"식단",
        r"셔틀",
        r"버스",
        r"좌석",
        r"열람실",
        r"도서관",
        r"강의실",
        r"전공\s*필수",
        r"전공\s*선택",
        r"교양",
        r"개설\s*학기",
    ]
    
    # Complex: 복잡한 추론/비교/추천 패턴
    COMPLEX_PATTERNS = [
        r"추천",
        r"어떤\s*것",
        r"좋을까",
        r"비교",
        r"차이",
        r"다른\s*점",
        r"분석",
        r"평가",
        r"왜",
        r"이유",
        r"원인",
        r"졸업\s*요건",
        r"학위",
        r"계획",
        r"전략",
        r"방법",
        r"어떻게",
    ]
    
    def classify(self, question: str) -> Literal["simple", "complex"]:
        """
        질문 분류
        
        Simple: 
        - 단순 정보 검색 (DB 쿼리 1-2회)
        - "자료구조 몇 학점?"
        - "전101 어디야?"
        - "오늘 학식 뭐야?"
        
        Complex:
        - 다단계 추론
        - 비교/분석
        - 추천/계획
        - "어떤 전공선택 들으면 좋을까?"
        - "졸업요건 확인해줘"
        
        Returns:
            "simple" or "complex"
        """
        question_lower = question.lower()
        
        # Simple 패턴 체크
        simple_count = 0
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, question):
                simple_count += 1
        
        # Complex 패턴 체크
        complex_count = 0
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, question):
                complex_count += 1
        
        # 패턴 기반 판단
        if complex_count > 0:
            return "complex"
        
        if simple_count > 0:
            return "simple"
        
        # 질문 길이 기반 휴리스틱
        if len(question) > 50:
            return "complex"
        
        # 물음표 개수 (여러 질문 = complex)
        if question.count("?") > 1:
            return "complex"
        
        # 기본값: simple (안전한 선택)
        return "simple"
    
    def get_classification_reason(self, question: str) -> str:
        """분류 이유 설명 (디버깅용)"""
        question_type = self.classify(question)
        
        reasons = []
        
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, question):
                reasons.append(f"Simple 패턴 발견: {pattern}")
        
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, question):
                reasons.append(f"Complex 패턴 발견: {pattern}")
        
        if len(question) > 50:
            reasons.append(f"질문 길이가 길음 ({len(question)}자)")
        
        if question.count("?") > 1:
            reasons.append(f"여러 질문 포함 ({question.count('?')}개)")
        
        if not reasons:
            reasons.append("기본값: simple")
        
        return f"{question_type.upper()} - " + ", ".join(reasons)


# 전역 인스턴스
classifier = QuestionClassifier()
