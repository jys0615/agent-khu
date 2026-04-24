"""
Prometheus 커스텀 메트릭 정의
- HTTP 메트릭: prometheus-fastapi-instrumentator 자동 수집
- 비즈니스 메트릭: 이 모듈에서 직접 정의
"""
from prometheus_client import Counter, Histogram, Gauge

# MCP tool 호출 수 (tool_name × status 조합)
mcp_tool_calls = Counter(
    "mcp_tool_calls_total",
    "MCP tool 호출 수",
    ["tool_name", "status"],   # status: success | error | cache_hit
)

# Agent 라우팅 결정 수
agent_routing = Counter(
    "agent_routing_total",
    "Agent 라우팅 결정 수",
    ["route"],                  # route: rag | llm | llm_fallback | fallback_direct
)

# Agent 전체 응답 레이턴시 (초 단위)
agent_latency = Histogram(
    "agent_response_latency_seconds",
    "Agent 응답 레이턴시",
    ["route"],
    buckets=[0.5, 1, 2, 5, 10, 30],
)

# 현재 활성 MCP 세션 수
mcp_active_sessions = Gauge(
    "mcp_active_sessions",
    "현재 활성 MCP 세션 수",
)
