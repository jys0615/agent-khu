"""
Phase 2 마이그레이션 Baseline 측정 스크립트
=============================================
목적: stdio 기반 MCP 현재 수치를 기록 → Phase 2(Streamable HTTP) 전환 후 비교

측정 항목:
  1. MCP 세션 cold start 시간 (서버별 subprocess spawn + initialize)
  2. Tool 호출 latency (warm session, 서버별 3회 평균)
  3. Memory: subprocess RSS (MiB)
  4. Tool discovery 시간 (list_tools 전체 서버)
  5. 동시 tool 호출 처리 시간 (asyncio.gather)

결과 저장: backend/scripts/results/phase2_baseline_<timestamp>.json
           backend/scripts/results/phase2_baseline_latest.json (항상 덮어씀)

사용법:
  cd backend
  python -m scripts.benchmarks.phase2_baseline
  # 또는
  python scripts/benchmarks/phase2_baseline.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median

import psutil

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
REPO_ROOT = BACKEND_DIR.parent
MCP_DIR = REPO_ROOT / "mcp-servers"
RESULTS_DIR = BACKEND_DIR / "scripts" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:password@localhost:5432/agent_khu")
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-for-benchmark")

from app.mcp_client import MCPClient, MCPServerSession  # noqa: E402

# ── 테스트 케이스 정의 ─────────────────────────────────────────────────────────
TOOL_TESTS: dict[str, list[tuple[str, dict]]] = {
    "classroom":  [
        ("search_classroom", {"query": "312"}),
        ("search_classroom", {"query": "전자정보대학관"}),
    ],
    "notice":     [
        ("search_notices", {"query": "장학", "limit": 3}),
        ("search_notices", {"query": "공지", "limit": 3}),
    ],
    "meal":       [
        ("get_today_meal", {"meal_type": "lunch"}),
        ("get_today_meal", {"meal_type": "dinner"}),
    ],
    "library":    [
        ("get_library_info", {"campus": "global"}),
    ],
    "curriculum": [
        ("search_curriculum", {"query": "자료구조", "year": "2024"}),
    ],
    "course":     [
        ("search_courses", {"department": "소프트웨어융합학과", "keyword": "프로그래밍"}),
    ],
    "shuttle":    [
        ("get_next_shuttle", {"route": "to_station"}),
    ],
}

CONCURRENT_TOOLS = [
    ("classroom",  "search_classroom", {"query": "312"}),
    ("meal",       "get_today_meal",   {"meal_type": "lunch"}),
    ("notice",     "search_notices",   {"query": "공지", "limit": 3}),
]


# ── 측정 헬퍼 ──────────────────────────────────────────────────────────────────

def _now_ms() -> float:
    return time.perf_counter() * 1000


async def measure_cold_start(client: MCPClient) -> dict[str, dict]:
    """각 MCP 서버 cold start 시간 측정 (순차, 재현성 확보)"""
    print("\n[1/4] Cold Start 측정 중...")
    results: dict[str, dict] = {}

    for name, session in client._sessions.items():
        t0 = _now_ms()
        try:
            await asyncio.wait_for(session.start(), timeout=30.0)
            elapsed = _now_ms() - t0
            results[name] = {"latency_ms": round(elapsed), "success": True}
            print(f"  ✓ {name}: {elapsed:.0f}ms")
        except Exception as e:
            elapsed = _now_ms() - t0
            results[name] = {"latency_ms": round(elapsed), "success": False, "error": str(e)}
            print(f"  ✗ {name}: {elapsed:.0f}ms — {e}")

    ok = [v["latency_ms"] for v in results.values() if v["success"]]
    print(f"  → 성공 {len(ok)}/{len(results)}  평균 {mean(ok):.0f}ms  중앙값 {median(ok):.0f}ms")
    return results


async def measure_tool_latency(client: MCPClient) -> dict[str, dict]:
    """Warm session 상태에서 tool 호출 latency 측정"""
    print("\n[2/4] Tool 호출 Latency 측정 중...")
    results: dict[str, dict] = {}

    for server, tests in TOOL_TESTS.items():
        session = client._sessions.get(server)
        if not session or session._session is None:
            results[server] = {"error": "session_unavailable", "calls": []}
            continue

        calls = []
        for tool, args in tests:
            t0 = _now_ms()
            try:
                await asyncio.wait_for(
                    session._session.call_tool(tool, args), timeout=10.0
                )
                elapsed = _now_ms() - t0
                calls.append({"tool": tool, "latency_ms": round(elapsed), "success": True})
                print(f"  ✓ {server}.{tool}: {elapsed:.0f}ms")
            except Exception as e:
                elapsed = _now_ms() - t0
                calls.append({"tool": tool, "latency_ms": round(elapsed), "success": False, "error": str(e)})
                print(f"  ✗ {server}.{tool}: {elapsed:.0f}ms — {e}")

        ok_latencies = [c["latency_ms"] for c in calls if c["success"]]
        results[server] = {
            "calls": calls,
            "avg_ms": round(mean(ok_latencies)) if ok_latencies else None,
            "min_ms": min(ok_latencies) if ok_latencies else None,
            "max_ms": max(ok_latencies) if ok_latencies else None,
        }

    all_ok = [c["latency_ms"] for v in results.values() for c in v.get("calls", []) if c.get("success")]
    if all_ok:
        print(f"  → 전체 평균 {mean(all_ok):.0f}ms  중앙값 {median(all_ok):.0f}ms")
    return results


def measure_subprocess_memory(client: MCPClient) -> dict[str, dict]:
    """활성 MCP subprocess RSS 메모리 측정"""
    print("\n[3/4] Subprocess 메모리 측정 중...")
    results: dict[str, dict] = {}
    current_proc = psutil.Process()
    children = current_proc.children(recursive=True)

    # 자식 프로세스 목록 출력 (디버그)
    child_pids = {p.pid: p for p in children}
    print(f"  자식 프로세스 수: {len(children)}")

    total_rss_mib = 0.0
    for name, session in client._sessions.items():
        if session._session is None:
            results[name] = {"rss_mib": None, "pid": None, "status": "no_session"}
            continue

        # MCPServerSession 내부 transport에서 PID 추출 시도
        pid = None
        try:
            # mcp stdio transport는 내부적으로 asyncio subprocess를 사용
            transport = getattr(session._exit_stack, "_exit_callbacks", [])
            # 대안: psutil로 python 자식 프로세스 중 server.py 포함한 것 탐색
            server_path = str(client.server_paths.get(name, ""))
            for child in children:
                try:
                    cmdline = " ".join(child.cmdline())
                    if server_path and server_path in cmdline:
                        pid = child.pid
                        break
                    # server_path 없을 경우 이름으로 매칭
                    if f"{name}-mcp" in cmdline or f"{name}_mcp" in cmdline:
                        pid = child.pid
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        if pid:
            try:
                p = psutil.Process(pid)
                rss_mib = p.memory_info().rss / 1024 / 1024
                total_rss_mib += rss_mib
                results[name] = {"rss_mib": round(rss_mib, 1), "pid": pid, "status": "ok"}
                print(f"  ✓ {name} (PID {pid}): {rss_mib:.1f} MiB")
            except Exception as e:
                results[name] = {"rss_mib": None, "pid": pid, "status": f"error: {e}"}
        else:
            results[name] = {"rss_mib": None, "pid": None, "status": "pid_not_found"}
            print(f"  ? {name}: PID 탐지 실패 (subprocess 구조상 한계)")

    # 전체 자식 프로세스 RSS 합산 (PID 탐지 실패 보완)
    total_children_rss = sum(
        p.memory_info().rss for p in children
        if p.is_running()
        for _ in [None]  # try/except 없이 안전하게
    ) if children else 0
    total_children_mib = total_children_rss / 1024 / 1024

    results["__summary__"] = {
        "subprocess_count": len(children),
        "total_children_rss_mib": round(total_children_mib, 1),
        "mcp_subprocess_rss_mib": round(total_rss_mib, 1),
    }
    print(f"  → 전체 자식 프로세스: {len(children)}개, 합산 RSS {total_children_mib:.1f} MiB")
    return results


async def measure_tool_discovery(client: MCPClient) -> dict:
    """list_tools() 전체 소요시간 측정"""
    print("\n[4/4] Tool Discovery 시간 측정 중...")
    t0 = _now_ms()
    try:
        tools = await client.discover_tools()
        elapsed = _now_ms() - t0
        print(f"  ✓ {len(tools)}개 tool 수집 완료: {elapsed:.0f}ms")
        return {
            "total_ms": round(elapsed),
            "tool_count": len(tools),
            "tools": [t["name"] for t in tools],
            "success": True,
        }
    except Exception as e:
        elapsed = _now_ms() - t0
        print(f"  ✗ 실패: {e}")
        return {"total_ms": round(elapsed), "success": False, "error": str(e)}


async def measure_concurrent_tools(client: MCPClient) -> dict:
    """asyncio.gather로 동시 tool 호출 시간 측정"""
    print("\n[+] 동시 Tool 호출 (asyncio.gather) 측정 중...")

    async def call_one(server: str, tool: str, args: dict) -> dict:
        session = client._sessions.get(server)
        if not session or session._session is None:
            return {"server": server, "tool": tool, "success": False, "error": "no_session"}
        t0 = _now_ms()
        try:
            await asyncio.wait_for(session._session.call_tool(tool, args), timeout=10.0)
            return {"server": server, "tool": tool, "latency_ms": round(_now_ms() - t0), "success": True}
        except Exception as e:
            return {"server": server, "tool": tool, "latency_ms": round(_now_ms() - t0), "success": False, "error": str(e)}

    t_total = _now_ms()
    results = await asyncio.gather(*[call_one(s, t, a) for s, t, a in CONCURRENT_TOOLS])
    total_elapsed = _now_ms() - t_total

    for r in results:
        status = "✓" if r.get("success") else "✗"
        print(f"  {status} {r['server']}.{r['tool']}: {r.get('latency_ms', '?')}ms")

    print(f"  → 동시 실행 총 소요: {total_elapsed:.0f}ms")
    return {
        "total_elapsed_ms": round(total_elapsed),
        "calls": list(results),
    }


# ── 메인 ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print(f"Phase 2 Baseline 측정  ({ts})")
    print(f"MCP_DIR: {MCP_DIR}")
    print("=" * 60)

    client = MCPClient()
    available = list(client._sessions.keys())
    print(f"\n등록된 MCP 서버: {available}")

    # 1. Cold Start
    cold_start = await measure_cold_start(client)

    # 2. Tool Latency (warm)
    tool_latency = await measure_tool_latency(client)

    # 3. Subprocess Memory
    memory = measure_subprocess_memory(client)

    # 4. Tool Discovery
    discovery = await measure_tool_discovery(client)

    # 5. Concurrent
    concurrent = await measure_concurrent_tools(client)

    # ── 요약 집계 ─────────────────────────────────────────────────────────────
    cold_ok = [v["latency_ms"] for v in cold_start.values() if v.get("success")]
    tool_all_ok = [
        c["latency_ms"]
        for v in tool_latency.values()
        for c in v.get("calls", [])
        if c.get("success")
    ]

    summary = {
        "measured_at": ts,
        "transport": "stdio",
        "phase": "before_phase2",
        "mcp_servers_registered": available,
        "cold_start": {
            "avg_ms": round(mean(cold_ok)) if cold_ok else None,
            "median_ms": round(median(cold_ok)) if cold_ok else None,
            "min_ms": min(cold_ok) if cold_ok else None,
            "max_ms": max(cold_ok) if cold_ok else None,
            "success_count": len(cold_ok),
            "total_count": len(cold_start),
        },
        "tool_latency_warm": {
            "avg_ms": round(mean(tool_all_ok)) if tool_all_ok else None,
            "median_ms": round(median(tool_all_ok)) if tool_all_ok else None,
            "min_ms": min(tool_all_ok) if tool_all_ok else None,
            "max_ms": max(tool_all_ok) if tool_all_ok else None,
            "sample_count": len(tool_all_ok),
        },
        "subprocess_memory": memory.get("__summary__", {}),
        "tool_discovery_ms": discovery.get("total_ms"),
        "tool_count": discovery.get("tool_count"),
        "concurrent_3tools_ms": concurrent.get("total_elapsed_ms"),
    }

    output = {
        "summary": summary,
        "detail": {
            "cold_start": cold_start,
            "tool_latency": tool_latency,
            "memory": memory,
            "tool_discovery": discovery,
            "concurrent": concurrent,
        },
    }

    # ── 저장 ──────────────────────────────────────────────────────────────────
    out_ts = RESULTS_DIR / f"phase2_baseline_{ts_file}.json"
    out_latest = RESULTS_DIR / "phase2_baseline_latest.json"

    for path in (out_ts, out_latest):
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 출력 ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 Phase 2 Baseline 요약 (stdio 기준)")
    print("=" * 60)
    s = summary
    print(f"  Cold Start  avg {s['cold_start']['avg_ms']}ms  "
          f"median {s['cold_start']['median_ms']}ms  "
          f"max {s['cold_start']['max_ms']}ms  "
          f"({s['cold_start']['success_count']}/{s['cold_start']['total_count']} 성공)")
    print(f"  Tool Latency avg {s['tool_latency_warm']['avg_ms']}ms  "
          f"median {s['tool_latency_warm']['median_ms']}ms  "
          f"min {s['tool_latency_warm']['min_ms']}ms  "
          f"max {s['tool_latency_warm']['max_ms']}ms")
    mem = s["subprocess_memory"]
    print(f"  Subprocess  {mem.get('subprocess_count', '?')}개  "
          f"합산 RSS {mem.get('total_children_rss_mib', '?')} MiB")
    print(f"  Tool Discovery {s['tool_discovery_ms']}ms  ({s['tool_count']} tools)")
    print(f"  동시 3 tools  {s['concurrent_3tools_ms']}ms")
    print(f"\n  결과 저장: {out_ts.name}")
    print("=" * 60)

    # anyio cancel scope가 asyncio.run() 이벤트 루프와 다른 태스크에서 닫히면
    # CancelledError가 발생하는 것은 mcp + anyio 라이브러리 한계 (FastAPI lifespan에서는 발생 안 함)
    try:
        await client.stop_all()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
