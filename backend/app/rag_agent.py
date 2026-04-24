"""
RAG Agent - Elasticsearch BM25 기반 Simple 질문 처리

SLM 파인튜닝 방식 대신 검색 기반으로 전환:
- 추가 GPU/모델 불필요
- 데이터 업데이트 → 재학습 없이 인덱스만 갱신
- 기존 Elasticsearch 인프라 재사용
- Simple 질문 응답 시 LLM 호출 없이 직접 반환 → API 비용 절감
"""
import os
import logging
from typing import Optional, Dict, Any, List
from elasticsearch import AsyncElasticsearch
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RAG_INDEX = "khu-rag-knowledge"
SCORE_THRESHOLD = 1.5   # BM25 점수 임계값 (이 이상이면 RAG 응답)
CONFIDENCE_SCALE = 8.0  # 점수 정규화 상수 (score / CONFIDENCE_SCALE → 0~1)
TOP_K = 3


class RAGAgent:
    """
    Elasticsearch BM25 기반 RAG Agent.

    Simple 질문 → ES 검색 → 관련 문서 있으면 LLM 없이 직접 반환
                           → 없으면 {"found": False} → agent_loop이 LLM으로 fallback
    """

    def __init__(self):
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es: Optional[AsyncElasticsearch] = None
        self.enabled = False
        self.index_name = RAG_INDEX

    async def initialize(self):
        """Elasticsearch 연결 및 인덱스 준비"""
        try:
            self.es = AsyncElasticsearch([self.es_url])

            if not await self.es.indices.exists(index=self.index_name):
                await self._create_index()
                logger.warning("RAG 인덱스 생성됨. 데이터 인덱싱 필요: python scripts/index_rag_data.py")
            else:
                count_result = await self.es.count(index=self.index_name)
                doc_count = count_result["count"]
                if doc_count > 0:
                    self.enabled = True
                    logger.info(f"RAG Agent 초기화 완료: {doc_count}개 문서")
                else:
                    logger.warning("RAG 인덱스 비어있음. 데이터 인덱싱 필요: python scripts/index_rag_data.py")

        except Exception as e:
            logger.warning(f"RAG Agent 초기화 실패 (LLM으로만 동작): {e}")
            self.enabled = False

    async def _create_index(self):
        """RAG 지식 인덱스 생성"""
        await self.es.indices.create(
            index=self.index_name,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                },
                "mappings": {
                    "properties": {
                        "doc_id":     {"type": "keyword"},
                        "category":   {"type": "keyword"},
                        "title":      {"type": "text"},
                        "content":    {"type": "text"},
                        "metadata":   {"type": "object", "enabled": False},
                        "indexed_at": {"type": "date"},
                        "expires_at": {"type": "date"},
                    }
                },
            },
        )

    async def close(self):
        if self.es:
            await self.es.close()

    async def search(
        self,
        question: str,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        BM25 검색으로 관련 문서 조회.

        Returns:
            {
                "found": bool,
                "answer": str,          # 직접 반환할 텍스트
                "confidence": float,    # 0.0 ~ 1.0
                "category": str,
                "sources": List[str],
            }
        """
        if not self.enabled or not self.es:
            return {"found": False, "confidence": 0.0}

        try:
            must_clauses: List[Dict] = [
                {
                    "multi_match": {
                        "query": question,
                        "fields": ["title^2", "content"],
                        "type": "best_fields",
                    }
                }
            ]

            filter_clauses: List[Dict] = []
            if category:
                filter_clauses.append({"term": {"category": category}})

            # 만료된 문서 제외 (expires_at 없으면 항상 유효)
            filter_clauses.append(
                {
                    "bool": {
                        "should": [
                            {"range": {"expires_at": {"gte": "now"}}},
                            {"bool": {"must_not": {"exists": {"field": "expires_at"}}}},
                        ]
                    }
                }
            )

            result = await self.es.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": must_clauses,
                            "filter": filter_clauses,
                        }
                    },
                    "size": TOP_K,
                    "_source": ["title", "content", "category", "metadata"],
                },
            )

            hits = result["hits"]["hits"]
            if not hits or hits[0]["_score"] < SCORE_THRESHOLD:
                return {"found": False, "confidence": 0.0}

            top_score = hits[0]["_score"]
            confidence = min(top_score / CONFIDENCE_SCALE, 1.0)

            # 상위 문서 내용 합산
            answer_parts = [h["_source"].get("content", "") for h in hits if h["_source"].get("content")]

            return {
                "found": True,
                "answer": "\n\n".join(answer_parts),
                "confidence": confidence,
                "category": hits[0]["_source"].get("category"),
                "sources": [h["_source"].get("title", "") for h in hits],
            }

        except Exception as e:
            logger.warning(f"RAG 검색 실패: {e}")
            return {"found": False, "confidence": 0.0}

    async def index_document(
        self,
        doc_id: str,
        category: str,
        title: str,
        content: str,
        metadata: Optional[Dict] = None,
        expires_at: Optional[str] = None,
    ) -> bool:
        """단일 문서 인덱싱 (upsert)"""
        if not self.es:
            return False
        try:
            doc: Dict[str, Any] = {
                "doc_id":     doc_id,
                "category":   category,
                "title":      title,
                "content":    content,
                "metadata":   metadata or {},
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
            if expires_at:
                doc["expires_at"] = expires_at

            await self.es.index(index=self.index_name, id=doc_id, document=doc)
            return True
        except Exception as e:
            logger.warning(f"RAG 인덱싱 실패 ({doc_id}): {e}")
            return False

    async def bulk_index(self, documents: List[Dict]) -> int:
        """
        다수 문서 일괄 인덱싱.

        documents 형식:
        [{"doc_id": str, "category": str, "title": str, "content": str,
          "metadata": dict, "expires_at": str(optional)}, ...]
        """
        if not self.es or not documents:
            return 0

        actions = []
        now = datetime.now(timezone.utc).isoformat()
        for doc in documents:
            actions.append({"index": {"_index": self.index_name, "_id": doc["doc_id"]}})
            body: Dict[str, Any] = {
                "doc_id":     doc["doc_id"],
                "category":   doc["category"],
                "title":      doc["title"],
                "content":    doc["content"],
                "metadata":   doc.get("metadata", {}),
                "indexed_at": now,
            }
            if doc.get("expires_at"):
                body["expires_at"] = doc["expires_at"]
            actions.append(body)

        try:
            response = await self.es.bulk(operations=actions, refresh=True)
            errors = [item for item in response.get("items", []) if "error" in item.get("index", {})]
            indexed = len(documents) - len(errors)
            if errors:
                logger.warning(f"RAG 벌크 인덱싱 일부 실패: {len(errors)}건")
            # 문서가 생겼으니 활성화
            if indexed > 0:
                self.enabled = True
            return indexed
        except Exception as e:
            logger.warning(f"RAG 벌크 인덱싱 실패: {e}")
            return 0

    async def delete_by_category(self, category: str) -> int:
        """카테고리 전체 삭제 (재인덱싱 전 호출)"""
        if not self.es:
            return 0
        try:
            result = await self.es.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"category": category}}},
                refresh=True,
            )
            return result.get("deleted", 0)
        except Exception as e:
            logger.warning(f"RAG 카테고리 삭제 실패 ({category}): {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """인덱스 통계"""
        if not self.es:
            return {"enabled": False}
        try:
            count_result = await self.es.count(index=self.index_name)
            agg_result = await self.es.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "aggs": {"by_category": {"terms": {"field": "category", "size": 20}}},
                },
            )
            buckets = agg_result["aggregations"]["by_category"]["buckets"]
            return {
                "enabled": self.enabled,
                "total_docs": count_result["count"],
                "by_category": {b["key"]: b["doc_count"] for b in buckets},
            }
        except Exception as e:
            return {"enabled": self.enabled, "error": str(e)}


# 싱글톤
_rag_agent: Optional[RAGAgent] = None


def get_rag_agent() -> RAGAgent:
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent()
    return _rag_agent
