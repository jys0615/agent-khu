"""
Observability Logger for Agent KHU
모든 사용자 상호작용을 Elasticsearch에 로깅하여 SLM 학습 데이터 수집
"""
from elasticsearch import Elasticsearch, AsyncElasticsearch
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import os
from contextlib import asynccontextmanager

class ObservabilityLogger:
    """모든 Agent 상호작용을 로깅"""
    
    def __init__(self, es_url: Optional[str] = None):
        self.es_url = es_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es: Optional[AsyncElasticsearch] = None
        self.index_name = "agent-khu-interactions"
        self.enabled = True
        
    async def initialize(self):
        """Elasticsearch 연결 초기화"""
        try:
            self.es = AsyncElasticsearch([self.es_url])
            
            # 인덱스 생성 (없으면)
            if not await self.es.indices.exists(index=self.index_name):
                await self.es.indices.create(
                    index=self.index_name,
                    body={
                        "mappings": {
                            "properties": {
                                "timestamp": {"type": "date"},
                                "question": {"type": "text"},
                                "user_id": {"type": "keyword"},
                                "question_type": {"type": "keyword"},
                                "routing_decision": {"type": "keyword"},
                                "mcp_tools_used": {"type": "keyword"},
                                "response": {"type": "text"},
                                "latency_ms": {"type": "integer"},
                                "success": {"type": "boolean"},
                                "error_message": {"type": "text"},
                                "metadata": {"type": "object", "enabled": False}
                            }
                        }
                    }
                )
                print(f"✅ Elasticsearch 인덱스 생성: {self.index_name}")
            
            print(f"✅ Elasticsearch 연결 성공: {self.es_url}")
            
        except Exception as e:
            print(f"⚠️ Elasticsearch 연결 실패 (로깅 비활성화): {e}")
            self.enabled = False
            self.es = None
    
    async def close(self):
        """연결 종료"""
        if self.es:
            await self.es.close()
    
    async def log_interaction(
        self,
        question: str,
        user_id: str,
        question_type: str,
        routing_decision: str,
        mcp_tools_used: List[str],
        response: str,
        latency_ms: int,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        사용자 상호작용 로깅
        
        Args:
            question: 사용자 질문
            user_id: 사용자 ID (익명이면 "anonymous")
            question_type: "simple" or "complex"
            routing_decision: "llm", "slm", "llm_fallback"
            mcp_tools_used: 사용된 MCP tool 목록
            response: Agent 응답
            latency_ms: 응답 시간 (밀리초)
            success: 성공 여부
            error_message: 에러 메시지 (실패 시)
            metadata: 추가 정보
        """
        if not self.enabled or not self.es:
            return
        
        try:
            doc = {
                "timestamp": datetime.utcnow().isoformat(),
                "question": question,
                "user_id": user_id,
                "question_type": question_type,
                "routing_decision": routing_decision,
                "mcp_tools_used": mcp_tools_used,
                "response": response,
                "latency_ms": latency_ms,
                "success": success,
                "error_message": error_message,
                "metadata": metadata or {}
            }
            
            await self.es.index(
                index=self.index_name,
                document=doc,
                refresh=False  # ✅ 추가: 즉시 refresh 안 함 (성능 향상)
            )
            
        except Exception as e:
            # 로깅 실패해도 메인 로직에 영향 없도록
            print(f"⚠️ Elasticsearch 로깅 실패: {e}")
    
    async def get_simple_queries(
        self,
        min_success: bool = True,
        max_latency_ms: int = 3000,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Simple 질문 로그 조회 (학습 데이터용)
        
        Args:
            min_success: 성공한 쿼리만
            max_latency_ms: 최대 응답 시간
            limit: 최대 결과 수
        """
        if not self.enabled or not self.es:
            return []
        
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"question_type": "simple"}},
                            {"term": {"success": True}} if min_success else {},
                            {"range": {"latency_ms": {"lte": max_latency_ms}}}
                        ]
                    }
                },
                "size": limit,
                "sort": [{"timestamp": {"order": "desc"}}]
            }
            
            result = await self.es.search(index=self.index_name, body=query)
            
            return [hit["_source"] for hit in result["hits"]["hits"]]
            
        except Exception as e:
            print(f"⚠️ Elasticsearch 쿼리 실패: {e}")
            return []


# 전역 인스턴스
obs_logger = ObservabilityLogger()
