"""
Complex query handler — Claude LLM + MCP Tool-Use 루프
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple

from anthropic import Anthropic
from .. import models
from ..config import get_settings
from .tools_definition import tools
from .tool_executor import process_tool_call
from .utils import detect_curriculum_intent, build_system_prompt
from .result_builder import (
    AccumulatedResults,
    empty_accumulated,
    accumulate_results,
    build_final_result,
)

log = logging.getLogger(__name__)

_client = Anthropic(api_key=get_settings().anthropic_api_key)
_MODEL = "claude-sonnet-4-20250514"
_MAX_ITERATIONS = 2


async def run_llm_agent(
    message: str,
    user_latitude: Optional[float],
    user_longitude: Optional[float],
    library_username: Optional[str],
    library_password: Optional[str],
    current_user: Optional[models.User],
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Claude Tool-Use 루프를 실행한다.

    Returns:
        (최종 결과 dict, 사용된 tool 이름 목록)

    Raises:
        예외는 호출자(agent_loop)에서 처리한다.
    """
    system_prompt = _make_system_prompt(message, current_user)
    messages: List[Dict] = [{"role": "user", "content": message}]
    accumulated: AccumulatedResults = empty_accumulated()
    tools_used: List[str] = []

    for iteration in range(1, _MAX_ITERATIONS + 1):
        log.debug("Agent iteration %d/%d", iteration, _MAX_ITERATIONS)

        response = _client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )

        if response.stop_reason == "tool_use":
            messages, tools_used = await _execute_tools(
                response, messages, accumulated, tools_used,
                user_latitude, user_longitude,
                library_username, library_password,
                current_user,
            )

        elif response.stop_reason == "end_turn":
            answer = _extract_text(response.content)
            log.info("Agent 완료 (tools=%s)", tools_used)
            return build_final_result(answer, accumulated), tools_used

        else:
            log.warning("예상치 못한 stop_reason: %s", response.stop_reason)
            break

    # 최대 반복 도달 — 마지막 응답에서 텍스트만 추출
    log.warning("Agent 최대 반복 횟수 도달 (%d)", _MAX_ITERATIONS)
    answer = _extract_text(response.content)
    return build_final_result(answer or "죄송합니다. 답변을 생성하지 못했습니다.", accumulated), tools_used


async def run_fallback(
    message: str,
    current_user: Optional[models.User],
) -> Optional[Dict[str, Any]]:
    """
    LLM 호출 실패 시 규칙 기반으로 MCP 도구를 직접 호출한다.
    현재는 졸업요건 질의만 처리하며, 처리 불가 시 None을 반환한다.
    """
    hint = detect_curriculum_intent(message)
    is_requirements_query = (
        hint.get("intent") == "requirements"
        or ("졸업" in message and "요건" in message)
    )
    if not is_requirements_query:
        return None

    res = await process_tool_call("get_requirements", {}, current_user=current_user)
    fb_tools = ["get_requirements"]

    if res and res.get("found") and isinstance(res.get("requirements"), dict):
        req = res["requirements"]
        try:
            msg = (
                f"## 📋 {req.get('year')}학번 "
                f"{req.get('program_name') or req.get('program')} 졸업요건 요약\n"
                f"- 총 이수학점: {req.get('total_credits')}학점\n"
                f"- 전공 이수학점: {req.get('major_credits')}학점"
            )
        except Exception:
            msg = "졸업요건 정보를 불러왔습니다."
        return {
            "message": msg,
            "requirements": req,
            "show_requirements": True,
            "_tools_used": fb_tools,
        }

    # MCP 실패 시 빈 누적 결과로 메시지 구성
    accumulated = empty_accumulated()
    accumulate_results(accumulated, "get_requirements", res or {})
    result = build_final_result("", accumulated)
    result["_tools_used"] = fb_tools
    if not result.get("message"):
        result["message"] = (res or {}).get("error") or "졸업요건 조회에 실패했습니다."
    return result


# ── private helpers ────────────────────────────────────────────────────────────

async def _execute_tools(
    response,
    messages: List[Dict],
    accumulated: AccumulatedResults,
    tools_used: List[str],
    user_latitude, user_longitude,
    library_username, library_password,
    current_user,
) -> Tuple[List[Dict], List[str]]:
    """Tool 호출 목록을 순차 실행하고 대화 이력을 갱신한다."""
    tool_calls = [c for c in response.content if c.type == "tool_use"]
    log.debug("%d개 Tool 순차 실행", len(tool_calls))

    tool_results = []
    for tool in tool_calls:
        log.debug("Tool 호출: %s", tool.name)
        tools_used.append(tool.name)

        result = await process_tool_call(
            tool.name, tool.input,
            user_latitude, user_longitude,
            library_username, library_password,
            current_user,
        )
        accumulate_results(accumulated, tool.name, result)
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
        await asyncio.sleep(0.1)  # MCP stdio 안정성 확보

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})
    return messages, tools_used


def _make_system_prompt(message: str, current_user: Optional[models.User]) -> str:
    hint = detect_curriculum_intent(message)
    hint_text = ""
    if hint.get("intent"):
        hint_text = f"\n[HINT] curriculum_intent={hint['intent']}\n"
    if hint.get("year"):
        hint_text += f"[HINT] requested_year={hint['year']}\n"
    return build_system_prompt(current_user, hint_text)


def _extract_text(content) -> str:
    return "".join(c.text for c in content if c.type == "text")
