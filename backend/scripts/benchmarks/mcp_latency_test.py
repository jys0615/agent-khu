import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Ensure backend package is importable
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.mcp_client import mcp_client

# Ensure DB URL points to local docker-postgres by default
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:password@localhost:5432/agent_khu")


async def measure_once(server: str, tool: str, args: dict, timeout: float = 5.0) -> dict:
    start = time.perf_counter()
    try:
        result = await mcp_client.call_tool(server, tool, args, timeout=timeout, retries=0)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # Try to stringify size info and sample
        try:
            serialized = json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
            payload_size = len(serialized)
            sample = serialized[:400]
        except Exception:
            payload_size = 0
            sample = ""
        return {
            "server": server,
            "tool": tool,
            "args": args,
            "success": True,
            "latency_ms": elapsed_ms,
            "payload_size": payload_size,
            "result_sample": sample
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "server": server,
            "tool": tool,
            "args": args,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": str(e)
        }


async def main():
    tests = [
        {"server": "classroom",  "tool": "search_classroom",          "args": {"query": "312"}},
        {"server": "notice",     "tool": "search_notices",           "args": {"query": "장학", "limit": 3}},
        {"server": "meal",       "tool": "get_today_meal",           "args": {"meal_type": "lunch"}},
        {"server": "library",    "tool": "get_library_info",         "args": {"campus": "global"}},
        {"server": "curriculum", "tool": "search_curriculum",        "args": {"query": "자료구조", "year": "2024"}},
        {"server": "course",     "tool": "search_courses",           "args": {"department": "소프트웨어융합학과", "keyword": "프로그래밍"}},
    ]

    results = []
    for t in tests:
        r = await measure_once(t["server"], t["tool"], t["args"])
        results.append(r)

    # Summary
    ok = [r for r in results if r.get("success")]
    fail = [r for r in results if not r.get("success")]
    avg_latency = int(sum(r["latency_ms"] for r in ok) / len(ok)) if ok else 0

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total": len(results),
        "success": len(ok),
        "failed": len(fail),
        "avg_latency_ms_success": avg_latency,
        "by_server": {}
    }

    from collections import defaultdict
    grp = defaultdict(list)
    for r in results:
        grp[r["server"]].append(r["latency_ms"])
    for s, arr in grp.items():
        summary["by_server"][s] = {
            "count": len(arr),
            "avg_latency_ms": int(sum(arr) / len(arr)),
            "min_ms": min(arr),
            "max_ms": max(arr)
        }

    logs_dir = BASE_DIR.parent / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_json = logs_dir / f'mcp_latency_{ts}.json'
    out_txt = logs_dir / f'mcp_latency_{ts}.txt'

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({"summary": summary, "items": results}, f, ensure_ascii=False, indent=2)

    lines = [
        f"총 {summary['total']}건, 성공 {summary['success']}, 실패 {summary['failed']}, 성공 평균 {summary['avg_latency_ms_success']}ms",
        "서버별 평균 지연:" 
    ]
    for s, v in summary["by_server"].items():
        lines.append(f" - {s}: avg {v['avg_latency_ms']}ms (min {v['min_ms']}, max {v['max_ms']})")
    lines.append("")
    for r in results:
        status = "OK" if r.get("success") else f"ERR: {r.get('error')}"
        lines.append(f"[{r['server']}.{r['tool']}] {r['latency_ms']}ms -> {status}")

    out_txt.write_text("\n".join(lines), encoding='utf-8')

    print(f"saved: {out_json}")
    print(f"saved: {out_txt}")


if __name__ == '__main__':
    asyncio.run(main())
