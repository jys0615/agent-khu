"""
통합 성능 벤치마크
모든 성능 지표를 하나의 JSON 파일에 저장
"""
import asyncio
import aiohttp
import json
import time
import redis
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev, median
from typing import Dict, List, Optional

# 테스트 쿼리 세트
TEST_QUERIES = {
    # 1. MCP 서버 개별 성능 (E2E를 통한 간접 측정)
    "mcp_by_server": {
        "curriculum": [
            "자료구조 과목 있어?",
            "알고리즘 과목 찾아줘",
            "프로그래밍 과목 뭐가 있지?",
        ],
        "notice": [
            "최신 공지사항을 보여줘",
            "장학금 공지사항 있어?",
            "학사 공지사항 알려줘",
        ],
        "meal": [
            "오늘 점심 메뉴는 뭐야?",
            "오늘 저녁 메뉴는?",
            "내일 아침 메뉴는?",
        ],
        "classroom": [
            "101호 찾아줄래?",
            "전자정보대학관 어디야?",
            "공학관 강의실 찾아줘",
        ],
    },
    
    # 2. E2E 응답 시간
    "e2e_simple_qa": [  # 도구 없음
        "안녕하세요",
        "감사합니다",
        "경희대학교는 어디에 있어?",
    ],
    
    "e2e_single_tool": [  # 단일 도구
        "오늘 점심 메뉴는 뭐야?",
        "최신 공지사항을 보여줘",
        "101호 찾아줄래?",
    ],
    
    "e2e_multi_tool": [  # 복합 쿼리 (2개)
        "자료구조 과목 있어?",
        "장학금 공지사항 있어?",
        "전자정보대학관 강의실은 어디 있어?",
    ],
    
    "e2e_advanced": [  # 복합 고급 (3개+)
        "3학기 수강할 과목 추천해줄래?",
        "CS 관련 과목들 뭐가 있지?",
    ],
    
    # 3. 캐시 성능 테스트
    "cache_test": [
        ("오늘 점심 메뉴는 뭐야?", 3),  # 같은 쿼리 3회
        ("최신 공지사항을 보여줘", 3),
    ],
}

# Redis 클라이언트
redis_client = None


def init_redis():
    """Redis 연결"""
    global redis_client
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        return True
    except:
        return False


async def test_mcp_by_query(server: str, message: str) -> dict:
    """MCP 서버를 간접적으로 측정 (E2E 통해)"""
    result = await test_e2e_chat(message)
    result["server"] = server
    return result


async def test_e2e_chat(message: str) -> dict:
    """E2E 채팅 테스트"""
    url = "http://localhost:8000/api/chat"
    payload = {"message": message}
    
    start = time.perf_counter()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "message": message,
                        "success": True,
                        "latency_ms": elapsed_ms,
                        "response_length": len(data.get("message", "")),
                    }
                else:
                    return {
                        "message": message,
                        "success": False,
                        "latency_ms": elapsed_ms,
                        "error": f"HTTP {resp.status}",
                    }
    except asyncio.TimeoutError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": "Timeout",
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": str(e)[:100],
        }


async def run_benchmark():
    """통합 벤치마크 실행"""
    print("🚀 통합 성능 벤치마크 시작\n")
    print("=" * 80)
    
    results = {
        "generated_at": datetime.now().isoformat(),
        "mcp_performance": {},
        "e2e_performance": {},
        "cache_performance": {},
        "stability": {},
    }
    
    # Redis 초기화
    redis_available = init_redis()
    print(f"Redis: {'✅ 연결' if redis_available else '❌ 미연결'}\n")
    
    # ========================================================================
    # 1. MCP 서버 개별 성능
    # ========================================================================
    print("1️⃣  MCP 서버 개별 성능 측정 중...")
    
    mcp_results = []
    for server, queries in TEST_QUERIES["mcp_by_server"].items():
        print(f"   📝 {server}...")
        for query in queries:
            print(f"      ▸ '{query[:30]}...'", end=" ", flush=True)
            result = await test_mcp_by_query(server, query)
            mcp_results.append(result)
            
            if result["success"]:
                print(f"✅ {result['latency_ms']}ms")
            else:
                print(f"❌ {result.get('error', 'Unknown')}")
    
    # 서버별 통계
    by_server = {}
    for result in mcp_results:
        server = result["server"]
        if server not in by_server:
            by_server[server] = {"latencies": [], "success": 0, "total": 0}
        
        by_server[server]["total"] += 1
        if result["success"]:
            by_server[server]["success"] += 1
            by_server[server]["latencies"].append(result["latency_ms"])
    
    for server, data in by_server.items():
        latencies = data["latencies"]
        results["mcp_performance"][server] = {
            "avg_latency_ms": int(mean(latencies)) if latencies else None,
            "min_latency_ms": min(latencies) if latencies else None,
            "max_latency_ms": max(latencies) if latencies else None,
            "success_rate": (data["success"] / data["total"] * 100) if data["total"] > 0 else 0,
            "total_calls": data["total"],
            "successful_calls": data["success"],
        }
    
    print()
    
    # ========================================================================
    # 2. E2E 응답 시간
    # ========================================================================
    print("2️⃣  E2E 응답 시간 측정 중...")
    
    # 간단한 QA
    print("   📝 간단한 QA (도구 없음)...")
    simple_results = []
    for msg in TEST_QUERIES["e2e_simple_qa"]:
        print(f"      ▸ '{msg[:30]}...'", end=" ", flush=True)
        result = await test_e2e_chat(msg)
        simple_results.append(result)
        if result["success"]:
            print(f"✅ {result['latency_ms']}ms")
        else:
            print(f"❌")
    
    # 단일 도구
    print("   📝 단일 Tool...")
    single_results = []
    for msg in TEST_QUERIES["e2e_single_tool"]:
        print(f"      ▸ '{msg[:30]}...'", end=" ", flush=True)
        result = await test_e2e_chat(msg)
        single_results.append(result)
        if result["success"]:
            print(f"✅ {result['latency_ms']}ms")
        else:
            print(f"❌")
    
    # 복합 쿼리
    print("   📝 복합 쿼리 (2개 Tool)...")
    multi_results = []
    for msg in TEST_QUERIES["e2e_multi_tool"]:
        print(f"      ▸ '{msg[:30]}...'", end=" ", flush=True)
        result = await test_e2e_chat(msg)
        multi_results.append(result)
        if result["success"]:
            print(f"✅ {result['latency_ms']}ms")
        else:
            print(f"❌")
    
    # 복합 고급
    print("   📝 복합 고급 (3개+ Tool)...")
    advanced_results = []
    for msg in TEST_QUERIES["e2e_advanced"]:
        print(f"      ▸ '{msg[:30]}...'", end=" ", flush=True)
        result = await test_e2e_chat(msg)
        advanced_results.append(result)
        if result["success"]:
            print(f"✅ {result['latency_ms']}ms")
        else:
            print(f"❌")
    
    # E2E 통계
    def calc_stats(results_list):
        success = [r for r in results_list if r["success"]]
        if not success:
            return None
        latencies = [r["latency_ms"] for r in success]
        return {
            "avg_ms": int(mean(latencies)),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "median_ms": int(median(latencies)),
            "success_rate": len(success) / len(results_list) * 100,
        }
    
    results["e2e_performance"] = {
        "simple_qa": calc_stats(simple_results),
        "single_tool": calc_stats(single_results),
        "multi_tool": calc_stats(multi_results),
        "advanced": calc_stats(advanced_results),
    }
    
    print()
    
    # ========================================================================
    # 3. 캐시 성능
    # ========================================================================
    print("3️⃣  캐시 성능 측정 중...")
    
    cache_results = []
    for query, repeat_count in TEST_QUERIES["cache_test"]:
        print(f"   📝 '{query[:30]}' × {repeat_count}회...")
        latencies = []
        
        for i in range(repeat_count):
            result = await test_e2e_chat(query)
            if result["success"]:
                latencies.append(result["latency_ms"])
                print(f"      {i+1}회: {result['latency_ms']}ms")
        
        if latencies:
            cache_results.append({
                "query": query,
                "latencies": latencies,
                "improvement": ((latencies[0] - latencies[-1]) / latencies[0] * 100) if len(latencies) > 1 else 0,
            })
    
    # 캐시 적중률 추정
    total_improvement = 0
    cache_hits = 0
    for item in cache_results:
        if item["improvement"] > 20:  # 20% 이상 빨라지면 캐시로 판단
            cache_hits += 1
        total_improvement += item["improvement"]
    
    results["cache_performance"] = {
        "cache_hit_rate": (cache_hits / len(cache_results) * 100) if cache_results else 0,
        "avg_improvement": total_improvement / len(cache_results) if cache_results else 0,
        "details": cache_results,
    }
    
    print()
    
    # ========================================================================
    # 4. 안정성
    # ========================================================================
    print("4️⃣  안정성 분석...")
    
    all_results = simple_results + single_results + multi_results + advanced_results + mcp_results
    total = len(all_results)
    successful = sum(1 for r in all_results if r.get("success"))
    timeouts = sum(1 for r in all_results if not r.get("success") and "Timeout" in str(r.get("error", "")))
    
    results["stability"] = {
        "tool_call_success_rate": (successful / total * 100) if total > 0 else 0,
        "timeout_count": timeouts,
        "error_rate": ((total - successful) / total * 100) if total > 0 else 0,
        "total_requests": total,
        "successful_requests": successful,
    }
    
    print(f"   성공률: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"   타임아웃: {timeouts}건")
    print(f"   오류율: {(total-successful)/total*100:.1f}%")
    
    # ========================================================================
    # 파일 저장
    # ========================================================================
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    out_file = logs_dir / f"unified_benchmark_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"✅ 벤치마크 완료")
    print(f"📁 결과: {out_file}")
    
    # 요약 출력
    print(f"\n{'=' * 80}")
    print("📊 요약")
    print("=" * 80)
    
    print("\n1️⃣  MCP 서버 개별 성능:")
    for server, perf in results["mcp_performance"].items():
        if perf["avg_latency_ms"]:
            print(f"   {server:12} | {perf['avg_latency_ms']:5}ms | 성공률 {perf['success_rate']:.0f}%")
    
    print("\n2️⃣  E2E 응답 시간:")
    for category, perf in results["e2e_performance"].items():
        if perf:
            print(f"   {category:12} | {perf['avg_ms']:5}ms | 범위 {perf['min_ms']}~{perf['max_ms']}ms")
    
    print(f"\n3️⃣  캐시 성능:")
    print(f"   적중률: {results['cache_performance']['cache_hit_rate']:.0f}%")
    print(f"   평균 개선: {results['cache_performance']['avg_improvement']:.0f}%")
    
    print(f"\n4️⃣  안정성:")
    print(f"   Tool 성공률: {results['stability']['tool_call_success_rate']:.1f}%")
    print(f"   타임아웃: {results['stability']['timeout_count']}건")
    print(f"   오류율: {results['stability']['error_rate']:.1f}%")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
