"""
QuestionClassifier 단위 테스트

목적:
  - Groq 교체 전 regex 동작을 golden set으로 고정 (회귀 방지)
  - async classify() 인터페이스 검증
  - 알려진 regex 오분류 케이스 문서화
"""
import pytest
from app.question_classifier import QuestionClassifier


@pytest.fixture
def clf_regex_only():
    """Groq 비활성화 — regex fallback 경로만 테스트"""
    clf = QuestionClassifier()
    clf._groq_enabled = False
    return clf


# ── regex fallback 단위 테스트 ───────────────────────────────────────────────

@pytest.mark.parametrize("question,expected", [
    # simple — 단순 정보 조회
    ("오늘 학식 뭐야?",              "simple"),
    ("전101 어디야?",                "simple"),
    ("셔틀 언제 와?",                "simple"),
    ("도서관 몇 시까지야?",           "simple"),
    ("자료구조 몇 학점이야?",          "simple"),
    ("오늘 저녁 메뉴 알려줘",         "simple"),
    ("전자정보대학관 위치가 어디야?",  "simple"),
    ("도서관 좌석 몇 개 남았어?",      "simple"),
    # complex — 추론·비교·추천
    ("어떤 전공선택을 들으면 좋을까?", "complex"),
    ("졸업요건 확인해줘",             "complex"),
    ("컴퓨터공학과 커리큘럼 분석해줘", "complex"),
    ("1학기와 2학기 수업 차이가 뭐야?","complex"),
])
def test_regex_correct_cases(clf_regex_only, question, expected):
    result = clf_regex_only._classify_with_regex(question)
    assert result == expected, (
        f"regex 오분류 — 질문: '{question}' | 예상: {expected} | 실제: {result}"
    )


# regex의 알려진 오분류 케이스 — Groq 전환이 수정하는 케이스들
# wrong_result: regex가 실제로 반환하는 잘못된 값 (문서화용)
@pytest.mark.parametrize("question,wrong_result", [
    ("강의실 위치 어떻게 가?", "complex"),  # '어떻게' → complex 오분류 (실제: simple)
    ("셔틀 어떻게 타?",       "complex"),  # '어떻게' → complex 오분류 (실제: simple)
    ("졸업까지 몇 학점 남았어?", "simple"), # '몇 학점' → simple 오분류 (실제: complex)
])
def test_regex_known_misclassification(clf_regex_only, question, wrong_result):
    """regex가 잘못 분류하는 케이스 문서화 — Groq 전환이 이를 수정"""
    result = clf_regex_only._classify_with_regex(question)
    assert result == wrong_result, (
        f"regex 오분류 동작이 변경됨 — 테스트를 업데이트하세요: '{question}' → '{result}'"
    )


# ── async classify 인터페이스 테스트 ─────────────────────────────────────────
# Groq API 없는 환경에서는 regex fallback이 동작 — CI에서도 통과

@pytest.mark.parametrize("question,expected", [
    ("오늘 학식 뭐야?",              "simple"),
    ("셔틀 언제 와?",                "simple"),
    ("자료구조 몇 학점이야?",          "simple"),
    ("졸업요건 확인해줘",             "complex"),
    ("어떤 전공선택을 들으면 좋을까?", "complex"),
])
async def test_classify_async_interface(clf_regex_only, question, expected):
    """async classify() 는 Groq 없이도 regex fallback으로 동작"""
    result = await clf_regex_only.classify(question)
    assert result == expected, (
        f"async classify 실패 — 질문: '{question}' | 예상: {expected} | 실제: {result}"
    )
