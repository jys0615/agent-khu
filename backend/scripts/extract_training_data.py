"""
Elasticsearch에서 SLM 학습 데이터 추출
"""
import asyncio
import json
from elasticsearch import AsyncElasticsearch
from datetime import datetime, timedelta


async def extract_simple_queries():
    """Simple 질문만 추출하여 JSONL 형식으로 저장"""
    
    es = AsyncElasticsearch(
        ["http://localhost:9200"],
        request_timeout=30
    )
    
    try:
        # Simple 질문만 필터링 (타임아웃 완화: 20초)
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"question_type": "simple"}},
                        {"term": {"success": True}},
                        {"range": {"latency_ms": {"lt": 20000}}}  # 20초 이내로 완화
                    ]
                }
            },
            "size": 10000,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        result = await es.search(index="agent-khu-interactions", body=query)
        
        training_data = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            
            # Instruction-following 포맷
            example = {
                "instruction": "경희대학교 학생을 위한 캠퍼스 정보를 제공하세요.",
                "input": source["question"],
                "output": source["response"],
                "tools_used": source.get("mcp_tools_used", []),
                "metadata": {
                    "latency_ms": source["latency_ms"],
                    "timestamp": source["timestamp"]
                }
            }
            training_data.append(example)
        
        # JSONL 저장
        output_file = "training_data.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for example in training_data:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")
        
        print(f"✅ {len(training_data)}개 학습 데이터 저장: {output_file}")
        
        if len(training_data) == 0:
            print("\n⚠️ 학습 데이터가 없습니다!")
            print("더 많은 대화를 수집하거나 타임아웃 조건을 완화하세요.")
            return
        
        print(f"\n통계:")
        print(f"  - Simple 질문: {len(training_data)}개")
        
        # Tool 사용 통계
        all_tools = []
        for ex in training_data:
            all_tools.extend(ex["tools_used"])
        
        from collections import Counter
        tool_counts = Counter(all_tools)
        print(f"\n가장 많이 사용된 Tools:")
        for tool, count in tool_counts.most_common(10):
            print(f"  - {tool}: {count}회")
    
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(extract_simple_queries())