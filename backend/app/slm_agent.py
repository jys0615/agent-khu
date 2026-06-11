"""
SLM Agent — 3계층 답변 생성

Layer 1. 템플릿 추출  — 구조화 데이터(학식·강의실·셔틀)에서 A: 파트 직접 추출
                        비용 0, 지연 0, 정확도 최고
Layer 2. Ollama 로컬  — 비구조화 텍스트(공지·졸업요건) 요약·생성
                        OLLAMA_URL 환경변수 필요, qwen2.5:1.5b 사용
Layer 3. Groq API     — Ollama 미실행 환경 fallback (llama-3.1-8b-instant)
                        GROQ_API_KEY 환경변수 필요

우선순위: 템플릿 → Ollama → Groq → 실패(RAG 원문 반환)
"""
import logging
import os
from typing import List, Optional, Dict, Any

import aiohttp

log = logging.getLogger(__name__)

# ── 템플릿 레이어 설정 ─────────────────────────────────────────────────────────
# 이 카테고리에서는 Q&A 문서에서 A: 파트를 추출해 바로 반환
_TEMPLATE_CATEGORIES = {"meal", "classroom", "shuttle", "library", "schedule"}

# ── 모델 설정 ─────────────────────────────────────────────────────────────────
_GROQ_MODEL = "llama-3.1-8b-instant"
_MAX_TOKENS = 512

_SYSTEM_PROMPT = (
    "경희대학교 AI 어시스턴트입니다.\n"
    "아래 참고 자료를 바탕으로 질문에 간결하고 정확하게 한국어로 답변하세요.\n"
    "참고 자료에 없는 내용은 모른다고 답하세요. 추측하지 마세요."
)


# ── Layer 1: 템플릿 추출 ───────────────────────────────────────────────────────

def _try_template(
    question: str,
    docs: List[str],
    category: str,
) -> Optional[str]:
    """Q: ... A: ... 형식 문서에서 답변 파트만 추출.

    구조화 데이터(학식·강의실·셔틀 등) 카테고리에서만 동작.
    추출 성공 시 자연어 답변 문자열 반환, 실패 시 None.
    """
    if category not in _TEMPLATE_CATEGORIES:
        return None

    for doc in docs:
        for sep in ("A:", "답변:", "Answer:"):
            if sep in doc:
                answer = doc.split(sep, 1)[1].strip()
                # 다음 Q: 블록이 있으면 그 앞까지만 사용
                for q_sep in ("Q:", "질문:"):
                    if q_sep in answer:
                        answer = answer.split(q_sep, 1)[0].strip()
                if len(answer) >= 10:
                    return answer

    return None


# ── Layer 2: Ollama 로컬 SLM ───────────────────────────────────────────────────

class _OllamaClient:
    """경량 Ollama HTTP 클라이언트 (aiohttp 기반)"""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def is_available(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as resp:
                    if resp.status != 200:
                        return False
                    data = await resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    available = any(self.model in m for m in models)
                    if not available:
                        log.info(
                            "Ollama 실행 중이지만 모델(%s) 없음. "
                            "다음 명령으로 설치: docker exec agent-khu-ollama "
                            "ollama pull %s",
                            self.model, self.model,
                        )
                    return available
        except Exception:
            return False

    async def generate(self, prompt: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    data = await resp.json()
                    return data.get("response", "").strip() or None
        except Exception as e:
            log.debug("Ollama 생성 실패: %s", e)
            return None


# ── Layer 3: Groq async ────────────────────────────────────────────────────────

class _GroqClient:
    """AsyncGroq 래퍼"""

    def __init__(self, api_key: str) -> None:
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=api_key)

    async def generate(self, system: str, user_content: str) -> Optional[str]:
        try:
            resp = await self._client.chat.completions.create(
                model=_GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=_MAX_TOKENS,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip() or None
        except Exception as e:
            log.warning("Groq 생성 실패: %s", e)
            return None


# ── SLMAgent ───────────────────────────────────────────────────────────────────

class SLMAgent:
    """3계층 SLM: 템플릿 → Ollama → Groq"""

    def __init__(self) -> None:
        self.enabled = False  # 하나 이상의 레이어가 활성화되면 True

        # Layer 2: Ollama
        self._ollama: Optional[_OllamaClient] = None
        ollama_url = os.getenv("OLLAMA_URL", "")
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        if ollama_url:
            self._ollama = _OllamaClient(ollama_url, ollama_model)
            self.enabled = True
            log.info("SLM Layer 2 (Ollama): %s — %s", ollama_url, ollama_model)

        # Layer 3: Groq
        self._groq: Optional[_GroqClient] = None
        try:
            from .config import get_settings
            api_key = get_settings().groq_api_key or os.getenv("GROQ_API_KEY", "")
        except Exception:
            api_key = os.getenv("GROQ_API_KEY", "")

        if api_key:
            try:
                self._groq = _GroqClient(api_key)
                self.enabled = True
                log.info("SLM Layer 3 (Groq): %s", _GROQ_MODEL)
            except Exception as e:
                log.warning("Groq 초기화 실패: %s", e)

        if not self.enabled:
            log.warning(
                "SLM Agent 비활성화: OLLAMA_URL 또는 GROQ_API_KEY 중 하나 이상 필요"
            )

    async def generate(
        self,
        question: str,
        context_docs: List[str],
        category: str = "",
    ) -> Dict[str, Any]:
        """
        3계층 순서로 답변 생성 시도.

        Returns:
            {"message": str, "confidence": float, "success": bool,
             "layer": "template"|"ollama"|"groq"}
        """
        if not context_docs:
            return {"message": "", "confidence": 0.0, "success": False}

        # ── Layer 1: 템플릿 추출 ───────────────────────────────────────────────
        template_answer = _try_template(question, context_docs, category)
        if template_answer:
            log.debug("SLM Layer 1 (template) 사용: category=%s", category)
            return {
                "message": template_answer,
                "confidence": 0.95,
                "success": True,
                "layer": "template",
            }

        # 공통 컨텍스트 문자열
        context = "\n\n".join(
            f"[자료 {i+1}]\n{doc}" for i, doc in enumerate(context_docs[:2])
        )

        # ── Layer 2: Ollama ────────────────────────────────────────────────────
        if self._ollama and await self._ollama.is_available():
            prompt = (
                f"{_SYSTEM_PROMPT}\n\n"
                f"[참고 자료]\n{context}\n\n"
                f"[질문]\n{question}\n\n"
                "[답변]"
            )
            answer = await self._ollama.generate(prompt)
            if answer:
                log.debug("SLM Layer 2 (Ollama) 사용")
                return {
                    "message": answer,
                    "confidence": self._evaluate(answer),
                    "success": True,
                    "layer": "ollama",
                }

        # ── Layer 3: Groq ──────────────────────────────────────────────────────
        if self._groq:
            user_content = f"[참고 자료]\n{context}\n\n[질문]\n{question}"
            answer = await self._groq.generate(_SYSTEM_PROMPT, user_content)
            if answer:
                log.debug("SLM Layer 3 (Groq) 사용")
                return {
                    "message": answer,
                    "confidence": self._evaluate(answer),
                    "success": True,
                    "layer": "groq",
                }

        return {"message": "", "confidence": 0.0, "success": False}

    def _evaluate(self, answer: str) -> float:
        """간단한 품질 점수 (0.0 ~ 1.0)"""
        score = 1.0
        if len(answer) < 10:
            score -= 0.4
        if any(w in answer for w in ["죄송", "모르겠", "알 수 없", "확인할 수 없"]):
            score -= 0.4
        words = answer.split()
        if len(words) > 10 and len(set(words)) / len(words) < 0.5:
            score -= 0.3
        return max(0.0, score)


# ── 싱글톤 ────────────────────────────────────────────────────────────────────
_instance: Optional[SLMAgent] = None


def get_slm_agent() -> SLMAgent:
    global _instance
    if _instance is None:
        _instance = SLMAgent()
    return _instance
