"""
SLM Agent — GitHub Models Phi-4 Mini Instruct (azure-ai-inference SDK)

역할: RAGAgent가 검색한 문서를 컨텍스트로 받아 Phi-4 Mini로 답변 생성.
     Simple 질문에서 Claude 호출 없이 응답 → 비용 절감.

전환 시: GITHUB_TOKEN → AZURE_AI_KEY, endpoint URL만 교체하면 됨.
"""
import os
import logging
from typing import Optional, Dict, Any, List

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

log = logging.getLogger(__name__)

_GITHUB_ENDPOINT = "https://models.inference.ai.azure.com"
_DEFAULT_MODEL = "Phi-4-mini-instruct"
_MAX_TOKENS = 512
_TEMPERATURE = 0.7

_SYSTEM_PROMPT = """경희대학교 AI 어시스턴트입니다.
아래 참고 자료를 바탕으로 질문에 간결하고 정확하게 답변하세요.
참고 자료에 없는 내용은 모른다고 답하세요. 추측하지 마세요."""


class SLMAgent:
    """
    GitHub Models Phi-4 Mini 기반 RAG 생성 에이전트.

    RAGAgent.search()가 반환한 docs를 컨텍스트로 주입하여 답변 생성.
    """

    def __init__(self) -> None:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("AZURE_AI_KEY")
        endpoint = os.getenv("AZURE_AI_ENDPOINT", _GITHUB_ENDPOINT)
        self.model = os.getenv("AZURE_SLM_MODEL", _DEFAULT_MODEL)
        self.enabled = False
        self._client: Optional[ChatCompletionsClient] = None

        if not token:
            log.warning("SLM Agent 비활성화: GITHUB_TOKEN 또는 AZURE_AI_KEY 없음")
            return

        try:
            self._client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(token),
            )
            self.enabled = True
            log.info("SLM Agent 초기화 완료: %s @ %s", self.model, endpoint)
        except Exception as e:
            log.warning("SLM Agent 초기화 실패: %s", e)

    async def generate(
        self,
        question: str,
        context_docs: List[str],
    ) -> Dict[str, Any]:
        """
        RAG 문서를 컨텍스트로 받아 Phi-4 Mini로 답변 생성.

        Args:
            question: 사용자 질문
            context_docs: RAGAgent.search()가 반환한 문서 원문 리스트

        Returns:
            {"message": str, "confidence": float, "success": bool}
        """
        if not self.enabled or not self._client:
            return {"message": "", "confidence": 0.0, "success": False}

        context = "\n\n".join(f"[자료 {i+1}]\n{doc}" for i, doc in enumerate(context_docs))
        user_content = f"[참고 자료]\n{context}\n\n[질문]\n{question}"

        try:
            response = self._client.complete(
                model=self.model,
                messages=[
                    SystemMessage(content=_SYSTEM_PROMPT),
                    UserMessage(content=user_content),
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
        """답변 품질 기반 신뢰도 산출 (0.0 ~ 1.0)"""
        score = 1.0
        if len(answer) < 10:
            score -= 0.4
        failure_words = ["죄송", "모르겠", "알 수 없", "확인할 수 없"]
        if any(w in answer for w in failure_words):
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
