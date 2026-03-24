"""
종합 성능 지표 측정
1. Tool 호출 성공률 (도구별)
2. 캐시 적중률 (Redis)
3. 졸업요건 확인 응답 시간 (특화 쿼리)
4. 타임아웃/오류율
"""
import asyncio
import aiohttp
import json
import time
import redis
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev, median
from typing import Dict, List

# 특화 테스트 쿼리
SPECIALIZED_QUERIES = [
    # 졸업요건
    ("졸업요건_1", "2024학번 컴퓨터공학부 졸업요건은?"),
    ("졸업요건_2", "졸업까지 몇 학점 필요해?"),
    
    # 캐시 적중 테스트 (같은 쿼리 반복)
    ("캐시_1회차_1", "오늘 점심 메뉴는 뭐야?"),
    ("캐시_1회차_2", "오늘 점심 메뉴는 뭐야?"),
    ("캐시_1회차_3", "오늘 점심 메뉴는 뭐야?"),
    
    # 공지사항 캐시 테스트
    ("캐시_공지_1", "최신 공지사항을 보여줘"),
    ("캐시_공지_2", "최신 공지사항을 보여줘"),
    
    # 타임아웃 경계 테스트
    ("복합_고급_1", "내년 1학기 수강신청할 과목 5개 추천하고 관련 공지사항도 알려줄래?"),
    ("복합_고급_2", "CS 과목들 중 고학점 나온 과목과 해당 시간에 강의실 위치 알려줄래?"),
]

# Redis 연결
redis_client = None


def init_redis():
    """Redis 연결 초기화"""
    global redis_client
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        return True
    except Exception as e:
        print(f"⚠️  Redis 연결 실패: {e}")
        return False


def get_redis_stats() -> Dict:
    """Redis 캐시 통계 수집"""
    if not redis_client:
        return {"available": False}
    
    try:
        info = redis_client.info('stats')
        keys_count = redis_client.dbsize()
        
        return {
            "available": True,
            "total_connections_received": info.get('total_connections_received', 0),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "expired_keys": info.get('expired_keys', 0),
            "evicted_keys": info.get('evicted_keys', 0),
            "db_keys": keys_count,
            "used_memory": info.get('used_memory_human', 'N/A'),
        }
    except Exception as e:
        print(f"⚠️  Redis 통계 수집 실패: {e}")
        return {"available": False, "error": str(e)}


async def test_chat_with_metrics(
    session: aiohttp.ClientSession, 
    query_name: str, 
    message: str,
    redis_before: dict
) -> dict:
    """도구 호출 상세 분석을 포함한 채팅 테스트"""
    url = "http://localhost:8000/api/chat"
    payload = {"message": message}
    
    redis_after = {}
    start_time = time.perf_counter()
    
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            
            if resp.status == 200:
                data = await resp.json()
                
                # Redis 상태 수집 (응답 후)
                if redis_client:
                    redis_after = get_redis_stats()
                
                # 도구 호출 분석
                tool_calls = []
                tool_call_count = 0
                if "tool_calls" in data:
                    tool_calls = data["tool_calls"]
                    tool_call_count = len(tool_calls)
                elif isinstance(data.get("message"), str):
                    # 응답에서 도구 호출 횟수 추정
                    msg = data["message"]
                    if "classroom" in msg.lower():
                        tool_calls.append("classroom")
                    if "meal" in msg.lower() or "menu" in msg.lower():
                        tool_calls.append("meal")
                    if "notice" in msg.lower() or "공지" in msg.lower():
                        tool_calls.append("notice")
                    if "curriculum" in msg.lower() or "과목" in msg.lower() or "교과" in msg.lower():
                        tool_calls.append("curriculum")
                    if "library" in msg.lower() or "도서관" in msg.lower():
                        tool_calls.append("library")
                    tool_call_count = len(tool_calls)
                
                # 캐시 적중 검증 (같은 쿼리면 더 빨라야 함)
                cache_hit = None
                if redis_before and redis_after:
                    try:
                        # 간단한 휴리스틱: 응답시간이 이전보다 30% 이상 빠르면 캐시 히트 추정
                        if "prev_latency_ms" in redis_before:
                            ratio = elapsed_ms / redis_before["prev_latency_ms"]
                            cache_hit = ratio < 0.7
                    except:
                        pass
                
                return {
                    "query_name": query_name,
                    "message": message,
                    "status": resp.status,
                    "success": True,
                    "latency_ms": elapsed_ms,
                    "response_length": len(data.get("message", "")),
                    "tool_calls": tool_calls,
                    "tool_call_count": tool_call_count,
                    "cache_hit_estimated": cache_hit,
                }
            else:
                return {
                    "query_name": query_name,
                    "message": message,
                    "status": resp.status,
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "error": f"HTTP {resp.status}",
                    "tool_calls": [],
                    "tool_call_count": 0,
                }
    except asyncio.TimeoutError:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query_name": query_name,
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": "Timeout (60s)",
            "tool_calls": [],
            "tool_call_count": 0,
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query_name": query_name,
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": str(e)[:100],
            "tool_calls": [],
            "tool_call_count": 0,
        }


async def main():
    """종합 성능 지표 측정"""
    print("🚀 종합 성능 지표 측정 시작\n")
    
    # Redis 초기화
    redis_available = init_redis()
    print(f"{'✅' if redis_available else '⚠️ '} Redis: {'연결됨' if redis_available else '미연결'}\n")
    
    redis_before = get_redis_stats() if redis_available else {}
    
    # 테스트 실행
    print(f"📝 {len(SPECIALIZED_QUERIES)}개 특화 쿼리 실행 중...\n")
    
    all_results = []
    prev_latency = 0
    
    async with aiohttp.ClientSession() as session:
        for query_name, message in SPECIALIZED_QUERIES:
            redis_state = {"prev_latency_ms": prev_latency}
            redis_state.update(redis_before)
            
            print(f"  ▸ {query_name}: '{message[:40]}...'", end=" ", flush=True)
            result = await test_chat_with_metrics(session, query_name, message, redis_state)
            all_results.append(result)
            
            if result["success"]:
                tool_str = f"(도구: {', '.join(result['tool_calls'][:2])})" if result['tool_calls'] else "(도구 없음)"
                cache_str = " [캐시?]" if result.get("cache_hit_estimated") else ""
                print(f"✅ {result['latency_ms']}ms {tool_str}{cache_str}")
                prev_latency = result['latency_ms']
            else:
                print(f"❌ {result['latency_ms']}ms ({result.get('error', 'Unknown')})")
    
    # Redis 최종 상태
    redis_after = get_redis_stats() if redis_available else {}
    
    # 통계 계산
    success_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]
    
    print(f"\n{'=' * 80}")
    print("📊 성능 지표 분석")
    print("=" * 80)
    
    # 1. Tool 호출 성공률
    print(f"\n1️⃣  Tool 호출 성공률")
    tool_stats = {}
    for result in success_results:
        for tool in result['tool_calls']:
            if tool not in tool_stats:
                tool_stats[tool] = {"success": 0, "total": 0}
            tool_stats[tool]["success"] += 1
            tool_stats[tool]["total"] += 1
    
    if tool_stats:
        for tool, stats in sorted(tool_stats.items()):
            rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {tool}: {stats['success']}/{stats['total']} ({rate:.0f}%)")
    else:
        print("   (도구 호출 데이터 없음)")
    
    # 2. 캐시 적중률 추정
    print(f"\n2️⃣  캐시 적중률 (추정)")
    cache_hits = sum(1 for r in success_results if r.get('cache_hit_estimated'))
    cache_candidates = sum(1 for r in success_results if r.get('cache_hit_estimated') is not None)
    if cache_candidates > 0:
        cache_rate = cache_hits / cache_candidates * 100
        print(f"   추정 히트: {cache_hits}/{cache_candidates} ({cache_rate:.0f}%)")
    else:
        print(f"   Redis 연결: {'✅' if redis_available else '❌'}")
        if redis_available:
            print(f"   Redis 메모리: {redis_after.get('used_memory', 'N/A')}")
            print(f"   DB 키 개수: {redis_after.get('db_keys', 0)}")
    
    # 3. 졸업요건 응답 시간
    print(f"\n3️⃣  졸업요건 확인 응답 시간")
    graduation_results = [r for r in success_results if "졸업" in r['query_name']]
    if graduation_results:
        times = [r['latency_ms'] for r in graduation_results]
        print(f"   호출: {len(times)}, 평균: {int(mean(times))}ms, 범위: {min(times)}~{max(times)}ms")
    else:
        print("   (데이터 없음)")
    
    # 4. 타임아웃 및 오류율
    print(f"\n4️⃣  오류 및 타임아웃 분석")
    timeout_count = sum(1 for r in failed_results if "Timeout" in r.get('error', ''))
    other_errors = len(failed_results) - timeout_count
    error_rate = (len(failed_results) / len(all_results) * 100) if all_results else 0
    
    print(f"   총 요청: {len(all_results)}")
    print(f"   성공: {len(success_results)} ({(len(success_results)/len(all_results)*100):.0f}%)")
    print(f"   타임아웃: {timeout_count}")
    print(f"   기타 오류: {other_errors}")
    print(f"   오류율: {error_rate:.1f}%")
    
    # 5. MCP 서버별 성능 (도구별 응답시간)
    if tool_stats:
        print(f"\n5️⃣  도구별 평균 응답 시간")
        tool_times = {}
        for result in success_results:
            for tool in result['tool_calls']:
                if tool not in tool_times:
                    tool_times[tool] = []
                tool_times[tool].append(result['latency_ms'])
        
        for tool in sorted(tool_times.keys()):
            times = tool_times[tool]
            print(f"   {tool}: {int(mean(times))}ms (범위: {min(times)}~{max(times)}ms)")
    
    # 6. 응답 시간 분포
    print(f"\n6️⃣  응답 시간 분포")
    if success_results:
        latencies = [r['latency_ms'] for r in success_results]
        print(f"   평균: {int(mean(latencies))}ms")
        print(f"   중앙값: {int(median(latencies))}ms")
        print(f"   P95: {int(sorted(latencies)[int(len(latencies)*0.95)])}ms" if len(latencies) > 1 else "   P95: N/A")
        print(f"   범위: {min(latencies)}~{max(latencies)}ms")
    
    # 파일 저장
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    out_json = logs_dir / f"comprehensive_metrics_{ts}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "test_queries": len(all_results),
            "success_count": len(success_results),
            "failed_count": len(failed_results),
            "tool_statistics": tool_stats,
            "cache_hit_rate": (cache_hits / cache_candidates * 100) if cache_candidates > 0 else None,
            "error_rate": error_rate,
            "redis_before": redis_before,
            "redis_after": redis_after,
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"✅ 측정 완료")
    print(f"📁 결과: {out_json}")


if __name__ == "__main__":
    asyncio.run(main())
