"""
Agent 메인 루프 — Simple/Complex 라우팅 및 Observability
"""
import time
import logging
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from .. import models
from ..observability import obs_logger
from ..question_classifier import classifier
from ..rag_agent import get_rag_agent
from .complex_handler import run_llm_agent, run_fallback

log = logging.getLogger(__name__)


async def chat_with_claude_async(
    message: str,
    db: Session,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    library_password: Optional[str] = None,
    current_user: Optional[models.User] = None,
) -> Dict[str, Any]:
    """
    Hybrid Agent 진입점.

    Simple 질문 → RAG (LLM 호출 없이 직접 응답)
    Complex 질문 또는 RAG 미매칭 → Claude Tool-Use 루프
    LLM 실패 → 규칙 기반 MCP 직접 호출 (Fallback)
    """
    start = time.time()
    question_type = classifier.classify(message)
    routing = "llm"
    tools_used: List[str] = []

    log.info("question_type=%s", question_type.upper())

    # ── Simple 경로: RAG ──────────────────────────────────────────────────────
    if question_type == "simple":
        rag = get_rag_agent()
        if rag.enabled:
            rag_result = await rag.search(message)
            if rag_result["found"] and rag_result["confidence"] >= 0.7:
                routing = "rag"
                await _log_interaction(
                    message, current_user, question_type, routing, [],
                    rag_result["answer"], start, success=True,
                    metadata={
                        "rag_confidence": rag_result["confidence"],
                        "rag_category": rag_result.get("category"),
                    },
                )
                return {"message": rag_result["answer"]}
        routing = "llm_fallback"

    # ── Complex 경로: LLM + Tool-Use ─────────────────────────────────────────
    log.info("LLM 처리 시작 (routing=%s)", routing)
    try:
        result, tools_used = await run_llm_agent(
            message, user_latitude, user_longitude,
            library_username, library_password, current_user,
        )
        await _log_interaction(
            message, current_user, question_type, routing,
            tools_used, result["message"], start, success=True,
        )
        return result

    except Exception as e:
        log.error("LLM Agent 에러: %s", e)

        # Fallback: 규칙 기반 MCP 직접 호출
        try:
            fb = await run_fallback(message, current_user)
            if fb:
                fb_tools = fb.pop("_tools_used", [])
                await _log_interaction(
                    message, current_user, question_type, "fallback_direct",
                    fb_tools, fb["message"], start, success=True,
                )
                return fb
        except Exception as fe:
            log.warning("Fallback 실패: %s", fe)

        await _log_interaction(
            message, current_user, question_type, routing,
            tools_used, str(e), start, success=False, error_message=str(e),
        )
        return {"message": "죄송합니다. 현재 연결이 원활하지 않습니다. 잠시 후 다시 시도해주세요."}


def chat_with_claude(
    message: str,
    db: Session,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
) -> Dict[str, Any]:
    """Sync 래퍼 (레거시 호환용)"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            chat_with_claude_async(message, db, user_latitude, user_longitude)
        )
    finally:
        loop.close()


# ── private helper ────────────────────────────────────────────────────────────

async def _log_interaction(
    question: str,
    user: Optional[models.User],
    question_type: str,
    routing: str,
    tools_used: List[str],
    response: str,
    start: float,
    success: bool,
    metadata: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> None:
    await obs_logger.log_interaction(
        question=question,
        user_id=user.student_id if user else "anonymous",
        question_type=question_type,
        routing_decision=routing,
        mcp_tools_used=tools_used,
        response=response,
        latency_ms=int((time.time() - start) * 1000),
        success=success,
        error_message=error_message,
        metadata=metadata,
    )
