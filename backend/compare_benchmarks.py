"""
MCP 벤치마크 vs E2E 응답 시간 분석
- MCP 개별 호출 시간 (mcp_benchmark.py 결과)
- E2E 전체 시간 (e2e_latency_test.py 결과)
- 오버헤드 분석
"""
import json
from pathlib import Path
from datetime import datetime

def main():
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    
    # 최신 벤치마크 파일 찾기
    mcp_files = sorted(logs_dir.glob("mcp_benchmark_*.json"), reverse=True)
    e2e_files = sorted(logs_dir.glob("e2e_latency_*.json"), reverse=True)
    
    if not mcp_files or not e2e_files:
        print("❌ 벤치마크 파일을 찾을 수 없습니다")
        return
    
    # 최신 파일 로드
    with open(mcp_files[0]) as f:
        mcp_data = json.load(f)
    
    with open(e2e_files[0]) as f:
        e2e_data = json.load(f)
    
    mcp_summary = mcp_data.get("summary", {})
    e2e_summary = e2e_data.get("summary", {})
    
    # 분석 결과
    print("=" * 100)
    print("성능 벤치마크 비교분석")
    print("=" * 100)
    
    print(f"\n📊 시간 범위 비교:")
    print(f"  MCP 개별 호출:    {mcp_summary['min_latency_ms']}ms ~ {mcp_summary['max_latency_ms']}ms (평균: {mcp_summary['avg_latency_ms']}ms)")
    print(f"  E2E 전체 응답:    {e2e_summary['min_latency_ms']}ms ~ {e2e_summary['max_latency_ms']}ms (평균: {e2e_summary['avg_latency_ms']}ms)")
    
    print(f"\n📈 통계 비교:")
    print(f"  지표                MCP 개별      E2E 전체      증가율")
    print(f"  {'-' * 55}")
    
    # 평균값
    mcp_avg = mcp_summary['avg_latency_ms']
    e2e_avg = e2e_summary['avg_latency_ms']
    ratio_avg = (e2e_avg / mcp_avg - 1) * 100
    print(f"  평균 응답 시간     {mcp_avg:5}ms      {e2e_avg:5}ms      {ratio_avg:+.1f}%")
    
    # 중앙값
    mcp_median = mcp_summary['median_latency_ms']
    e2e_median = e2e_summary['median_latency_ms']
    ratio_median = (e2e_median / mcp_median - 1) * 100
    print(f"  중앙값 (P50)       {mcp_median:5}ms      {e2e_median:5}ms      {ratio_median:+.1f}%")
    
    # P95
    mcp_p95 = mcp_summary.get('p95_latency_ms', mcp_summary['max_latency_ms'])
    e2e_p95 = e2e_summary['p95_latency_ms']
    ratio_p95 = (e2e_p95 / mcp_p95 - 1) * 100
    print(f"  P95 (상위 5%)      {mcp_p95:5}ms      {e2e_p95:5}ms      {ratio_p95:+.1f}%")
    
    print(f"\n🔍 오버헤드 분석:")
    
    # Agent loop 오버헤드 (평균)
    agent_overhead = e2e_avg - mcp_avg
    overhead_ratio = (agent_overhead / e2e_avg * 100)
    
    print(f"  E2E 평균 응답: {e2e_avg}ms")
    print(f"  MCP 평균 호출: {mcp_avg}ms")
    print(f"  추정 Agent 오버헤드: {agent_overhead:.0f}ms ({overhead_ratio:.1f}%)")
    print(f"    → Claude API 호출, 프롬프트 구성, 도구 디스패칭, JSON 파싱 등")
    
    print(f"\n📋 MCP 서버별 성능:")
    mcp_by_server = mcp_data.get("by_server", {})
    for server, stats in sorted(mcp_by_server.items(), key=lambda x: x[1]['avg_latency_ms']):
        print(f"  {server:15} | 평균: {stats['avg_latency_ms']:5}ms | 범위: {stats['min_latency_ms']}~{stats['max_latency_ms']}ms | 호출: {stats['total']}")
    
    print(f"\n🔬 쿼리 유형별 E2E 응답 시간:")
    e2e_results = e2e_data.get("results", [])
    by_type = {}
    for result in e2e_results:
        if result.get("success"):
            category = result["query_name"].split("_")[0]
            if category not in by_type:
                by_type[category] = []
            by_type[category].append(result["latency_ms"])
    
    for category in sorted(by_type.keys()):
        times = by_type[category]
        avg = sum(times) / len(times)
        print(f"  {category:15} | {len(times)} 호출 | 평균: {avg:.0f}ms | 범위: {min(times)}~{max(times)}ms")
    
    print(f"\n💡 최적화 제안:")
    print(f"  1. Agent 루프 오버헤드 {agent_overhead:.0f}ms는 Claude API 호출에서 대부분 발생")
    print(f"     → 응답시간의 {overhead_ratio:.0f}%를 차지")
    print(f"     → MCP 병렬 호출, 프로세스 풀 재사용으로 개선 가능")
    
    # 느린 MCP 찾기
    slowest_server = max(mcp_by_server.items(), key=lambda x: x[1]['avg_latency_ms'])[0]
    slowest_time = mcp_by_server[slowest_server]['avg_latency_ms']
    print(f"\n  2. {slowest_server} MCP가 가장 느림 ({slowest_time}ms)")
    if slowest_server == "notice":
        print(f"     → 웹 크롤링 최적화 고려")
    elif slowest_server == "curriculum":
        print(f"     → 데이터 캐싱 구조 개선")
    
    # 느린 쿼리 타입
    slowest_type = max(by_type.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]
    slowest_e2e = sum(by_type[slowest_type]) / len(by_type[slowest_type])
    print(f"\n  3. '{slowest_type}' 쿼리가 가장 느림 ({slowest_e2e:.0f}ms)")
    print(f"     → 여러 MCP 도구를 순차 호출할 가능성")
    print(f"     → 주요 도구를 먼저 호출하도록 에이전트 프롬프트 조정")
    
    print(f"\n  4. 도서관/교과과정 조회가 30초 이상 → 사전 캐싱 고려")
    print(f"     → Redis 캐시 TTL 증가 (현재 1시간)")
    print(f"     → 백그라운드 크롤러로 주기적 업데이트")
    
    print(f"\n✅ 분석 완료")
    print(f"  MCP 벤치마크: {mcp_files[0].name}")
    print(f"  E2E 벤치마크: {e2e_files[0].name}")


if __name__ == "__main__":
    main()
