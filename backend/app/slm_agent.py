"""
SLM Agent — Groq API (Llama 3.1 8B)

역할: RAGAgent가 검색한 문서를 컨텍스트로 받아 답변 생성.
     Simple 질문에서 Claude 호출 없이 응답 → 비용 절감.
"""
import os
import logging
from typing import Optional, Dict, Any, List

from groq import Groq
from .config import get_settings

log = logging.getLogger(__name__)

_MODEL = "llama-3.1-8b-instant"
_MAX_TOKENS = 512
_TEMPERATURE = 0.7

_SYSTEM_PROMPT = """경희대학교 AI 어시스턴트입니다.
아래 참고 자료를 바탕으로 질문에 간결하고 정확하게 답변하세요.
참고 자료에 없는 내용은 모른다고 답하세요. 추측하지 마세요."""


class SLMAgent:
    def __init__(self) -> None:
        api_key = get_settings().groq_api_key or os.getenv("GROQ_API_KEY")
        self.enabled = False
        self._client: Optional[Groq] = None

        if not api_key:
            log.warning("SLM Agent 비활성화: GROQ_API_KEY 없음")
            return

        try:
            self._client = Groq(api_key=api_key)
            self.enabled = True
            log.info("SLM Agent 초기화 완료: %s", _MODEL)
        except Exception as e:
            log.warning("SLM Agent 초기화 실패: %s", e)

    async def generate(self, question: str, context_docs: List[str]) -> Dict[str, Any]:
        if not self.enabled or not self._client:
            return {"message": "", "confidence": 0.0, "success": False}

        context = "\n\n".join(f"[자료 {i+1}]\n{doc}" for i, doc in enumerate(context_docs))
        user_content = f"[참고 자료]\n{context}\n\n[질문]\n{question}"

        try:
            response = self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=_MAX_TOKENS,
                temperature=_TEMPERATURE,
            )
            answer = response.choices[0].message.content.strip()
            confidence = self._evaluate(answer)
            return {"message": answer, "confidence": confidence, "success": True}

        except Exception as e:
            log.warning("SLM 생성 실패: %s", e)
            return {"message": "", "confidence": 0.0, "success": False, "error": str(e)}

    def _evaluate(self, answer: str) -> float:
        score = 1.0
        if len(answer) < 10:
            score -= 0.4
        if any(w in answer for w in ["죄송", "모르겠", "알 수 없", "확인할 수 없"]):
            score -= 0.4
        words = answer.split()
        if len(words) > 10 and len(set(words)) / len(words) < 0.5:
            score -= 0.3
        return max(0.0, score)


_instance: Optional[SLMAgent] = None


def get_slm_agent() -> SLMAgent:
    global _instance
    if _instance is None:
        _instance = SLMAgent()
    return _instance
