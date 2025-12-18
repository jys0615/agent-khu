import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev, median
import sys

# Ensure backend package is importable
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.mcp_client import mcp_client


# 각 MCP 서버별 테스트 케이스 (name, tool, args)
MCP_TESTS = {
    "classroom": [
        ("search_classroom", {"query": "101호"}),
        ("search_classroom", {"query": "312"}),
        ("search_classroom", {"query": "강의실"}),
    ],
    "notice": [
        ("search_notices", {"query": "장학", "limit": 3}),
        ("search_notices", {"query": "공지", "limit": 5}),
        ("search_notices", {"query": "신청", "limit": 3}),
    ],
    "meal": [
        ("get_today_meal", {"meal_type": "lunch"}),
        ("get_today_meal", {"meal_type": "breakfast"}),
        ("get_today_meal", {"meal_type": "dinner"}),
    ],
    "library": [
        ("get_library_info", {"campus": "global"}),
        ("get_library_info", {"campus": "global"}),
        ("get_library_info", {"campus": "global"}),
    ],
    "curriculum": [
        ("search_curriculum", {"query": "자료구조", "year": "2024"}),
        ("search_curriculum", {"query": "프로그래밍", "year": "2024"}),
        ("search_curriculum", {"query": "AI", "year": "2024"}),
    ],
}


async def measure_mcp_call(server: str, tool: str, args: dict, timeout: float = 5.0) -> dict:
    """단일 MCP 호출 측정"""
    start = time.perf_counter()
    try:
        result = await mcp_client.call_tool(server, tool, args, timeout=timeout, retries=0)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        
        # 결과 크기 측정
        try:
            payload_size = len(json.dumps(result, ensure_ascii=False))
        except Exception:
            payload_size = 0
        
        return {
            "server": server,
            "tool": tool,
            "success": True,
            "latency_ms": elapsed_ms,
            "payload_size": payload_size,
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "server": server,
            "tool": tool,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": str(e)[:100],
        }


async def main():
    """MCP 서버별 벤치마크 실행"""
    all_results = []
    
    # 각 서버별 테스트 실행
    for server, tests in MCP_TESTS.items():
        print(f"\n🔧 {server.upper()} MCP 벤치마크 시작...")
        server_results = []
        
        for tool, args in tests:
            print(f"  ▸ {tool}({json.dumps(args)})...", end=" ", flush=True)
            result = await measure_mcp_call(server, tool, args)
            server_results.append(result)
            all_results.append(result)
            
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['latency_ms']}ms")
    
    # 통계 계산
    by_server = {}
    for server in MCP_TESTS.keys():
        server_calls = [r for r in all_results if r["server"] == server]
        success_calls = [r for r in server_calls if r["success"]]
        
        if success_calls:
            latencies = [r["latency_ms"] for r in success_calls]
            by_server[server] = {
                "total": len(server_calls),
                "success": len(success_calls),
                "failed": len(server_calls) - len(success_calls),
                "avg_latency_ms": int(mean(latencies)),
                "median_latency_ms": int(median(latencies)),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "stdev_latency_ms": int(stdev(latencies)) if len(latencies) > 1 else 0,
                "p95_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]),
            }
        else:
            by_server[server] = {
                "total": len(server_calls),
                "success": 0,
                "failed": len(server_calls),
                "error": "모든 호출 실패"
            }
    
    # 전체 통계
    success_all = [r for r in all_results if r["success"]]
    if success_all:
        all_latencies = [r["latency_ms"] for r in success_all]
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total": len(all_results),
            "success": len(success_all),
            "failed": len(all_results) - len(success_all),
            "avg_latency_ms": int(mean(all_latencies)),
            "median_latency_ms": int(median(all_latencies)),
            "min_latency_ms": min(all_latencies),
            "max_latency_ms": max(all_latencies),
            "stdev_latency_ms": int(stdev(all_latencies)) if len(all_latencies) > 1 else 0,
        }
    else:
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total": len(all_results),
            "success": 0,
            "failed": len(all_results),
            "error": "모든 호출 실패"
        }
    
    # 파일 저장
    logs_dir = BASE_DIR.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    out_json = logs_dir / f"mcp_benchmark_{ts}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "by_server": by_server,
            "all_calls": all_results
        }, f, ensure_ascii=False, indent=2)
    
    # 텍스트 리포트
    out_txt = logs_dir / f"mcp_benchmark_{ts}.txt"
    lines = [
        "=" * 70,
        "MCP 서버별 평균 응답시간 벤치마크",
        "=" * 70,
        f"생성일시: {summary['generated_at']}",
        f"총 호출: {summary['total']}, 성공: {summary['success']}, 실패: {summary['failed']}",
        "",
        "📊 전체 통계",
        f"  평균: {summary.get('avg_latency_ms', 'N/A')}ms",
        f"  중앙값: {summary.get('median_latency_ms', 'N/A')}ms",
        f"  최소: {summary.get('min_latency_ms', 'N/A')}ms",
        f"  최대: {summary.get('max_latency_ms', 'N/A')}ms",
        f"  표준편차: {summary.get('stdev_latency_ms', 'N/A')}ms",
        "",
        "📈 서버별 상세 통계",
    ]
    
    for server in sorted(by_server.keys()):
        stats = by_server[server]
        if "error" in stats:
            lines.append(f"\n{server.upper()}: {stats['error']}")
        else:
            lines.append(f"\n{server.upper()}")
            lines.append(f"  호출: {stats['total']} (성공: {stats['success']}, 실패: {stats['failed']})")
            lines.append(f"  평균: {stats['avg_latency_ms']}ms")
            lines.append(f"  중앙값: {stats['median_latency_ms']}ms")
            lines.append(f"  범위: {stats['min_latency_ms']}ms ~ {stats['max_latency_ms']}ms")
            lines.append(f"  P95: {stats['p95_latency_ms']}ms")
            lines.append(f"  표준편차: {stats['stdev_latency_ms']}ms")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("상세 호출 기록")
    lines.append("=" * 70)
    for call in all_results:
        status = "✅" if call["success"] else "❌"
        if call["success"]:
            lines.append(f"{status} {call['server']}.{call['tool']}: {call['latency_ms']}ms (크기: {call['payload_size']} bytes)")
        else:
            lines.append(f"{status} {call['server']}.{call['tool']}: {call['error']}")
    
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    
    print(f"\n✅ 벤치마크 완료")
    print(f"📄 JSON: {out_json}")
    print(f"📄 텍스트: {out_txt}")
    print(f"\n🎯 요약:")
    print(f"   총 호출: {summary['total']}, 성공: {summary['success']}, 실패: {summary['failed']}")
    print(f"   평균 응답: {summary.get('avg_latency_ms', 'N/A')}ms")
    print(f"   범위: {summary.get('min_latency_ms', 'N/A')}ms ~ {summary.get('max_latency_ms', 'N/A')}ms")


if __name__ == "__main__":
    asyncio.run(main())
