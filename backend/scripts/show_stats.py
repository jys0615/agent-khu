"""
수집된 데이터 통계 조회
"""
import asyncio
from elasticsearch import AsyncElasticsearch


async def show_stats():
    es = AsyncElasticsearch(
        ["http://localhost:9200"],
        request_timeout=30
    )
    
    try:
        # 전체 개수
        count = await es.count(index="agent-khu-interactions")
        print(f"📊 총 수집된 대화: {count['count']}개\n")
        
        # Question Type 분포
        agg_query = {
            "size": 0,
            "aggs": {
                "by_type": {
                    "terms": {"field": "question_type"}
                },
                "avg_latency_by_type": {
                    "terms": {"field": "question_type"},
                    "aggs": {
                        "avg_ms": {"avg": {"field": "latency_ms"}}
                    }
                },
                "tools": {
                    "terms": {"field": "mcp_tools_used", "size": 20}
                }
            }
        }
        
        result = await es.search(index="agent-khu-interactions", **agg_query)
        
        print("📈 질문 타입별 분포:")
        for bucket in result["aggregations"]["by_type"]["buckets"]:
            print(f"  - {bucket['key']}: {bucket['doc_count']}개")
        
        print("\n⏱️ 타입별 평균 응답 시간:")
        for bucket in result["aggregations"]["avg_latency_by_type"]["buckets"]:
            avg_ms = bucket["avg_ms"]["value"]
            print(f"  - {bucket['key']}: {avg_ms:.0f}ms ({avg_ms/1000:.1f}초)")
        
        print("\n🔧 가장 많이 사용된 Tools:")
        for bucket in result["aggregations"]["tools"]["buckets"][:10]:
            print(f"  - {bucket['key']}: {bucket['doc_count']}회")
    
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(show_stats())