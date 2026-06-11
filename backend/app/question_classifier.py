"""
Question Classifier — Simple / Complex 라우팅 결정

개선 (Phase 1):
  - classify()를 async로 전환
  - Groq llama-3.1-8b-instant 기반 분류 (있으면 우선 사용)
  - Groq 미설정 또는 실패 시 regex fallback (기존 로직 유지)

Groq 도입 효과:
  - "강의실 위치 어떻게 가?" → regex: complex(오분류) / Groq: simple(정확)
  - '어떻게' 같은 ambiguous 패턴의 문맥 이해 가능
  - latency ~200ms (llama-3.1-8b-instant, max_tokens=5)
"""
import re
import logging
from typing import Literal, Optional

log = logging.getLogger(__name__)


class QuestionClassifier:
    """질문을 simple / complex로 분류"""

    # ── regex 패턴 (Groq fallback용) ─────────────────────────────────────────
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

    def __init__(self) -> None:
        self._groq_enabled = False
        self._groq_client = None

        try:
            from .config import get_settings
            api_key = get_settings().groq_api_key
        except Exception:
            api_key = ""

        if api_key:
            try:
                from groq import AsyncGroq
                self._groq_client = AsyncGroq(api_key=api_key)
                self._groq_enabled = True
                log.info("QuestionClassifier: Groq 기반 분류기 활성화")
            except Exception as e:
                log.warning("QuestionClassifier: Groq 초기화 실패, regex fallback 사용: %s", e)
        else:
            log.info("QuestionClassifier: GROQ_API_KEY 없음 — regex fallback 모드")

    # ── public API ────────────────────────────────────────────────────────────

    async def classify(self, question: str) -> Literal["simple", "complex"]:
        """질문 분류 (async).

        1순위: Groq llama-3.1-8b-instant (문맥 이해)
        2순위: regex fallback (Groq 미설정 또는 실패 시)
        """
        if self._groq_enabled:
            try:
                return await self._classify_with_groq(question)
            except Exception as e:
                log.debug("Groq 분류 실패, regex fallback: %s", e)

        return self._classify_with_regex(question)

    def get_classification_reason(self, question: str) -> str:
        """분류 이유 설명 (디버깅용 — regex 기준)"""
        question_type = self._classify_with_regex(question)
        reasons = []
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, question):
                reasons.append(f"Simple 패턴: {pattern}")
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, question):
                reasons.append(f"Complex 패턴: {pattern}")
        if len(question) > 50:
            reasons.append(f"질문 길이 {len(question)}자")
        if question.count("?") > 1:
            reasons.append("복수 질문")
        if not reasons:
            reasons.append("기본값: simple")
        return f"{question_type.upper()} — " + ", ".join(reasons)

    # ── private ───────────────────────────────────────────────────────────────

    async def _classify_with_groq(self, question: str) -> Literal["simple", "complex"]:
        """Groq API 기반 분류 — 문맥 이해 가능"""
        resp = await self._groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "다음 질문을 분류해. 단어 하나(simple 또는 complex)만 답해.\n\n"
                    "- simple: 단순 정보 조회 "
                    "(예: 학식 메뉴, 강의실 위치, 셔틀 시간, 도서관 운영시간)\n"
                    "- complex: 추론·비교·추천·분석이 필요한 질문 "
                    "(예: 졸업요건 분석, 과목 추천, 커리큘럼 비교)\n\n"
                    f"질문: {question}"
                ),
            }],
            max_tokens=5,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip().lower()
        if "simple" in answer:
            return "simple"
        if "complex" in answer:
            return "complex"
        # 불명확 응답 → regex로 재판정
        log.debug("Groq 응답 불명확('%s'), regex로 재판정", answer)
        return self._classify_with_regex(question)

    def _classify_with_regex(self, question: str) -> Literal["simple", "complex"]:
        """regex 기반 분류 — Groq fallback 및 단위 테스트용"""
        simple_count = sum(
            1 for p in self.SIMPLE_PATTERNS if re.search(p, question)
        )
        complex_count = sum(
            1 for p in self.COMPLEX_PATTERNS if re.search(p, question)
        )

        if complex_count > 0:
            return "complex"
        if simple_count > 0:
            return "simple"
        if len(question) > 50:
            return "complex"
        if question.count("?") > 1:
            return "complex"
        return "simple"


# ── 전역 인스턴스 ──────────────────────────────────────────────────────────────
classifier = QuestionClassifier()
