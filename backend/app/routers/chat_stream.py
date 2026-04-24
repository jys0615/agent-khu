"""
Streamable HTTP 채팅 엔드포인트 (MCP 2025-03-26 표준)

POST /api/chat/stream
  - Accept: text/event-stream  → SSE 실시간 스트림 반환
  - Accept: application/json   → 완료 후 단일 JSON 반환 (폴백)
"""
import asyncio
import json
import logging
import uuid
from typing import Optional, AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse

from ..agent.complex_handler import run_llm_agent_stream
from ..auth import get_current_user_optional
from .. import models, schemas

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat-stream"])

# tool name → 한국어 상태 메시지
TOOL_LABELS: dict[str, str] = {
    "get_classroom_info":      "강의실 정보 조회 중...",
    "get_cafeteria_menu":      "학식 메뉴 확인 중...",
    "get_library_seats":       "도서관 좌석 조회 중...",
    "get_shuttle_info":        "셔틀버스 정보 확인 중...",
    "get_notices":             "공지사항 불러오는 중...",
    "get_courses":             "강의 목록 검색 중...",
    "get_requirements":        "졸업요건 불러오는 중...",
    "get_evaluation":          "성적 평가 기준 확인 중...",
    "reserve_library_seat":    "도서관 좌석 예약 중...",
}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_events(
    message: str,
    latitude: Optional[float],
    longitude: Optional[float],
    library_username: Optional[str],
    library_password: Optional[str],
    current_user: Optional[models.User],
    session_id: str,
) -> AsyncIterator[str]:
    """asyncio.Queue 경유로 on_event 콜백 → SSE 변환."""
    queue: asyncio.Queue = asyncio.Queue()

    async def on_event(event: dict) -> None:
        await queue.put(event)

    async def _run() -> None:
        try:
            result, tools_used = await run_llm_agent_stream(
                message, latitude, longitude,
                library_username, library_password,
                current_user, on_event,
            )
            await queue.put({"type": "done", "result": result, "tools_used": tools_used})
        except Exception as e:
            log.error("Stream agent 에러: %s", e)
            await queue.put({"type": "error", "message": str(e)})

    task = asyncio.create_task(_run())

    # 초기 연결 확인 이벤트
    yield _sse({"type": "connected", "session_id": session_id})

    while True:
        event = await queue.get()
        event_type = event.get("type")

        if event_type == "text":
            yield _sse(event)

        elif event_type == "tool_start":
            tool_name = event.get("tool", "")
            label = TOOL_LABELS.get(tool_name, f"{tool_name} 실행 중...")
            yield _sse({"type": "tool_start", "tool": tool_name, "label": label})

        elif event_type == "tool_end":
            yield _sse({"type": "tool_end", "tool": event.get("tool", "")})

        elif event_type == "done":
            yield _sse({"type": "done", "result": event["result"]})
            break

        elif event_type == "error":
            yield _sse({"type": "error", "message": event.get("message", "알 수 없는 오류")})
            break

    await task


@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    body: schemas.ChatRequest,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Streamable HTTP 채팅 엔드포인트.
    Accept 헤더가 text/event-stream이면 SSE 스트림, 그 외엔 JSON 단일 응답.
    """
    session_id = str(uuid.uuid4())
    accept = request.headers.get("accept", "")

    if "text/event-stream" in accept:
        headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Mcp-Session-Id": session_id,
        }
        return StreamingResponse(
            _stream_events(
                body.message,
                body.latitude,
                body.longitude,
                body.library_username,
                body.library_password,
                current_user,
                session_id,
            ),
            media_type="text/event-stream",
            headers=headers,
        )

    # JSON 폴백: 스트리밍 없이 완료 후 반환
    try:
        result_holder: dict = {}
        tools_holder: list = []

        async def noop(_event: dict) -> None:
            pass

        result, tools_used = await run_llm_agent_stream(
            body.message, body.latitude, body.longitude,
            body.library_username, body.library_password,
            current_user, noop,
        )
        return JSONResponse(content=result)
    except Exception as e:
        log.error("JSON 폴백 에러: %s", e)
        return JSONResponse(
            status_code=500,
            content={"message": "죄송합니다. 오류가 발생했습니다.", "error": str(e)},
        )
