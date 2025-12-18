"""
End-to-End 채팅 응답 시간 측정
사용자 질문 → 백엔드 처리 → 응답 반환까지 전체 시간 측정
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev, median

# 테스트할 질문 세트
# 카테고리: 간단한 질문, MCP 도구 호출, 복합 쿼리
CHAT_QUERIES = [
    # 1. 간단한 질문 (SLM/캐시 가능)
    ("간단한_정보", "경희대학교 국제캠퍼스는 어디에 있어?"),
    ("인사_1", "안녕하세요"),
    ("감사_1", "감사합니다"),
    
    # 2. 공지사항/식사 정보 (MCP 도구)
    ("공지사항", "최신 공지사항을 보여줘"),
    ("장학금", "장학금 공지사항 있어?"),
    ("학식", "오늘 점심 메뉴는 뭐야?"),
    
    # 3. 강의실/위치 검색
    ("강의실", "101호 찾아줄래?"),
    ("강의실_2", "전자정보대학관 강의실은 어디 있어?"),
    
    # 4. 도서관 좌석 (로그인 필요, 오류 가능성)
    ("도서관", "도서관 좌석 현황 봐줄래?"),
    
    # 5. 교과과정 (curriculum MCP)
    ("교과과정", "자료구조 과목 있어?"),
    ("교과과정_2", "프로그래밍 과목 찾아줘"),
    
    # 6. 복합 쿼리
    ("복합_1", "3학기 수강할 과목 추천해줄래?"),
    ("복합_2", "CS 관련 과목들 뭐가 있지?"),
]


async def test_chat_latency(session: aiohttp.ClientSession, query_name: str, message: str) -> dict:
    """단일 채팅 쿼리 응답 시간 측정"""
    url = "http://localhost:8000/api/chat"
    payload = {"message": message}
    
    start_time = time.perf_counter()
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            
            if resp.status == 200:
                data = await resp.json()
                response_len = len(json.dumps(data, ensure_ascii=False))
                
                return {
                    "query_name": query_name,
                    "message": message,
                    "status": resp.status,
                    "success": True,
                    "latency_ms": elapsed_ms,
                    "response_size": response_len,
                    "response_length": len(data.get("message", "")),
                }
            else:
                return {
                    "query_name": query_name,
                    "message": message,
                    "status": resp.status,
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "error": f"HTTP {resp.status}",
                }
    except asyncio.TimeoutError:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query_name": query_name,
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": "Timeout (60s)",
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query_name": query_name,
            "message": message,
            "success": False,
            "latency_ms": elapsed_ms,
            "error": str(e)[:100],
        }


async def main():
    """E2E 응답 시간 벤치마크 실행"""
    print("🚀 E2E 채팅 응답 시간 측정 시작\n")
    print(f"⚠️  주의: 백엔드 서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print(f"    docker-compose up 으로 서버를 시작해주세요.\n")
    
    # 서버 연결 확인
    async with aiohttp.ClientSession() as session:
        for attempt in range(5):
            try:
                async with session.get("http://localhost:8000/api/auth/me", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    print(f"✅ 백엔드 서버 응답 확인 (상태: {resp.status})")
                    break
            except Exception as e:
                if attempt < 4:
                    print(f"⏳ 서버 연결 대기 ({attempt + 1}/5)... {e}")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ 서버 연결 실패: {e}")
                    print(f"   docker-compose up 으로 백엔드를 시작해주세요.")
                    return
    
    # 테스트 실행
    print(f"\n📝 {len(CHAT_QUERIES)}개 쿼리 실행 중...\n")
    
    all_results = []
    async with aiohttp.ClientSession() as session:
        for query_name, message in CHAT_QUERIES:
            print(f"  ▸ {query_name}: '{message[:40]}...'", end=" ", flush=True)
            result = await test_chat_latency(session, query_name, message)
            all_results.append(result)
            
            if result["success"]:
                print(f"✅ {result['latency_ms']}ms (응답 {result['response_length']}자)")
            else:
                print(f"❌ {result['latency_ms']}ms ({result.get('error', 'Unknown')})")
    
    # 통계 계산
    success_results = [r for r in all_results if r["success"]]
    
    if not success_results:
        print("\n❌ 모든 요청 실패")
        return
    
    latencies = [r["latency_ms"] for r in success_results]
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": len(all_results),
        "successful": len(success_results),
        "failed": len(all_results) - len(success_results),
        "avg_latency_ms": int(mean(latencies)),
        "median_latency_ms": int(median(latencies)),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "stdev_latency_ms": int(stdev(latencies)) if len(latencies) > 1 else 0,
        "p50_latency_ms": int(sorted(latencies)[len(latencies) // 2]),
        "p95_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.95)]) if len(latencies) > 1 else max(latencies),
        "p99_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.99)]) if len(latencies) > 1 else max(latencies),
    }
    
    # 파일 저장
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    out_json = logs_dir / f"e2e_latency_{ts}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    
    # 텍스트 리포트
    out_txt = logs_dir / f"e2e_latency_{ts}.txt"
    lines = [
        "=" * 80,
        "End-to-End 채팅 응답 시간 벤치마크",
        "=" * 80,
        f"생성일시: {summary['generated_at']}",
        f"총 쿼리: {summary['total_queries']}, 성공: {summary['successful']}, 실패: {summary['failed']}",
        "",
        "📊 응답 시간 통계 (밀리초)",
        f"  평균: {summary['avg_latency_ms']}ms",
        f"  중앙값 (P50): {summary['median_latency_ms']}ms",
        f"  최소: {summary['min_latency_ms']}ms",
        f"  최대: {summary['max_latency_ms']}ms",
        f"  표준편차: {summary['stdev_latency_ms']}ms",
        f"  P95: {summary['p95_latency_ms']}ms (상위 5% 응답 시간)",
        f"  P99: {summary['p99_latency_ms']}ms (상위 1% 응답 시간)",
        "",
        "📈 상세 결과",
    ]
    
    # 카테고리별 분석
    category_stats = {}
    for result in success_results:
        category = result["query_name"].split("_")[0]
        if category not in category_stats:
            category_stats[category] = []
        category_stats[category].append(result["latency_ms"])
    
    lines.append("")
    lines.append("카테고리별 분석:")
    for category in sorted(category_stats.keys()):
        times = category_stats[category]
        lines.append(f"\n  {category}:")
        lines.append(f"    호출: {len(times)}, 평균: {int(mean(times))}ms, 범위: {min(times)}~{max(times)}ms")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("개별 결과")
    lines.append("=" * 80)
    
    for result in all_results:
        if result["success"]:
            lines.append(f"✅ {result['query_name']:15} | {result['latency_ms']:5}ms | Q: '{result['message'][:40]}'")
        else:
            error = result.get("error", "Unknown")
            lines.append(f"❌ {result['query_name']:15} | {result['latency_ms']:5}ms | {error}")
    
    out_txt.write_text("\n".join(lines), encoding="utf-8")
    
    # 콘솔 출력
    print("\n" + "=" * 80)
    print("✅ E2E 벤치마크 완료")
    print("=" * 80)
    print(f"\n📊 응답 시간 통계:")
    print(f"   평균: {summary['avg_latency_ms']}ms")
    print(f"   중앙값: {summary['median_latency_ms']}ms")
    print(f"   범위: {summary['min_latency_ms']}ms ~ {summary['max_latency_ms']}ms")
    print(f"   P95: {summary['p95_latency_ms']}ms")
    print(f"   P99: {summary['p99_latency_ms']}ms")
    
    print(f"\n📁 결과 저장:")
    print(f"   JSON: {out_json}")
    print(f"   TXT: {out_txt}")
    
    print(f"\n카테고리별 평균 응답:")
    for category in sorted(category_stats.keys()):
        times = category_stats[category]
        print(f"   {category}: {int(mean(times))}ms")


if __name__ == "__main__":
    asyncio.run(main())
