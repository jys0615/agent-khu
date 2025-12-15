#!/usr/bin/env python3
"""
Agent KHU 평가 지표 분석 스크립트
Elasticsearch 로그 또는 로컬 JSON 결과를 분석하여 지표 생성
"""
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics
from collections import defaultdict

try:
    from elasticsearch import Elasticsearch
except ImportError:
    print("⚠️ elasticsearch 라이브러리 미설치: pip install elasticsearch")
    Elasticsearch = None


class MetricsAnalyzer:
    def __init__(self, es_url: Optional[str] = None, raw_results: Optional[List[Dict]] = None):
        self.es_url = es_url or "http://localhost:9200"
        self.es = None
        self.raw_results = raw_results or []
        self.index_name = "agent-khu-interactions"
        self._connect_es()
    
    def _connect_es(self):
        """Elasticsearch 연결"""
        if not Elasticsearch:
            print("⚠️ Elasticsearch 사용 불가 (라이브러리 미설치)")
            return
        
        try:
            self.es = Elasticsearch([self.es_url])
            if self.es.ping():
                print(f"✅ Elasticsearch 연결: {self.es_url}")
            else:
                self.es = None
                print(f"⚠️ Elasticsearch 핑 실패")
        except Exception as e:
            print(f"⚠️ Elasticsearch 연결 실패: {e}")
            self.es = None
    
    def fetch_logs_from_es(self, limit: int = 10000) -> List[Dict]:
        """Elasticsearch에서 최근 로그 조회"""
        if not self.es:
            print("⚠️ Elasticsearch 미연결: 로컬 데이터만 사용")
            return []
        
        try:
            query = {
                "query": {"match_all": {}},
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            result = self.es.search(index=self.index_name, body=query)
            
            docs = [hit["_source"] for hit in result["hits"]["hits"]]
            print(f"✅ ES에서 {len(docs)}개 로그 조회")
            return docs
        
        except Exception as e:
            print(f"⚠️ ES 쿼리 실패: {e}")
            return []
    
    def analyze(self) -> Dict[str, Any]:
        """전체 분석 수행"""
        # 로그 데이터 확보
        if self.es:
            logs = self.fetch_logs_from_es()
        else:
            logs = self._transform_raw_results()
        
        if not logs:
            print("❌ 분석할 로그가 없습니다")
            return {}
        
        print(f"\n📊 {len(logs)}개 로그로 분석 시작")
        
        metrics = {
            "metadata": {
                "total_samples": len(logs),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "elasticsearch" if self.es else "local"
            },
            "overall": self._analyze_overall(logs),
            "by_domain": self._analyze_by_domain(logs),
            "latency": self._analyze_latency(logs),
            "tools": self._analyze_tools(logs),
            "routing": self._analyze_routing(logs)
        }
        
        return metrics
    
    def _transform_raw_results(self) -> List[Dict]:
        """로컬 평가 결과를 로그 포맷으로 변환"""
        logs = []
        for result in self.raw_results:
            if result.get("status") == "success":
                logs.append({
                    "question": result.get("question", ""),
                    "success": True,
                    "latency_ms": result.get("latency_ms", 0),
                    "question_type": self._infer_type(result.get("domain", "")),
                    "routing_decision": "llm",  # 기본값
                    "mcp_tools_used": result.get("tools_used", []),
                    "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                    "domain": result.get("domain", "unknown")
                })
            else:
                logs.append({
                    "question": result.get("question", ""),
                    "success": False,
                    "latency_ms": result.get("latency_ms", 0),
                    "question_type": self._infer_type(result.get("domain", "")),
                    "error_message": result.get("error", ""),
                    "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                    "domain": result.get("domain", "unknown")
                })
        return logs
    
    def _infer_type(self, domain: str) -> str:
        """도메인을 question_type으로 변환"""
        if domain in ["classroom", "curriculum", "notice", "library", "meal", "shuttle"]:
            return "simple"
        return "complex"
    
    def _analyze_overall(self, logs: List[Dict]) -> Dict:
        """전체 성공률, 지연 등"""
        success_count = sum(1 for log in logs if log.get("success", False))
        total = len(logs)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        latencies = [log.get("latency_ms", 0) for log in logs if log.get("success", False)]
        
        return {
            "success_rate": round(success_rate, 2),
            "success_count": success_count,
            "total": total,
            "failed_count": total - success_count,
            "failed_rate": round(100 - success_rate, 2)
        }
    
    def _analyze_by_domain(self, logs: List[Dict]) -> Dict:
        """도메인별 분석"""
        by_domain = defaultdict(list)
        
        for log in logs:
            domain = log.get("domain", "unknown")
            by_domain[domain].append(log)
        
        result = {}
        for domain, domain_logs in by_domain.items():
            success = sum(1 for log in domain_logs if log.get("success", False))
            total = len(domain_logs)
            latencies = [log.get("latency_ms", 0) for log in domain_logs if log.get("success", False)]
            
            result[domain] = {
                "total": total,
                "success": success,
                "success_rate": round(success / total * 100, 2) if total > 0 else 0,
                "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
                "p50_latency_ms": round(statistics.median(latencies), 2) if latencies else 0,
                "p95_latency_ms": round(self._percentile(latencies, 95), 2) if latencies else 0
            }
        
        return result
    
    def _analyze_latency(self, logs: List[Dict]) -> Dict:
        """지연 분석"""
        latencies = [log.get("latency_ms", 0) for log in logs if log.get("success", False)]
        
        if not latencies:
            return {"error": "No successful requests"}
        
        sorted_latencies = sorted(latencies)
        
        return {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": round(statistics.mean(latencies), 2),
            "median_ms": round(statistics.median(latencies), 2),
            "p50_ms": round(self._percentile(latencies, 50), 2),
            "p95_ms": round(self._percentile(latencies, 95), 2),
            "p99_ms": round(self._percentile(latencies, 99), 2),
            "stdev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0
        }
    
    def _analyze_tools(self, logs: List[Dict]) -> Dict:
        """Tool 사용 분석"""
        tool_counts = []
        all_tools = defaultdict(int)
        
        for log in logs:
            if log.get("success", False):
                tools = log.get("mcp_tools_used", [])
                if isinstance(tools, list):
                    tool_counts.append(len(tools))
                    for tool in tools:
                        all_tools[tool] += 1
        
        return {
            "avg_tools_per_request": round(statistics.mean(tool_counts), 2) if tool_counts else 0,
            "max_tools": max(tool_counts) if tool_counts else 0,
            "zero_tool_requests": sum(1 for c in tool_counts if c == 0),
            "zero_tool_rate": round(sum(1 for c in tool_counts if c == 0) / len(tool_counts) * 100, 2) if tool_counts else 0,
            "most_used_tools": dict(sorted(all_tools.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _analyze_routing(self, logs: List[Dict]) -> Dict:
        """라우팅 결정 분석"""
        routing_counts = defaultdict(int)
        
        for log in logs:
            decision = log.get("routing_decision", "unknown")
            routing_counts[decision] += 1
        
        total = sum(routing_counts.values())
        
        return {
            "distribution": {k: round(v / total * 100, 2) for k, v in routing_counts.items()} if total > 0 else {},
            "counts": dict(routing_counts)
        }
    
    @staticmethod
    def _percentile(values: List[float], p: int) -> float:
        """백분위수 계산"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def print_report(self, metrics: Dict):
        """보고서 출력"""
        print("\n" + "=" * 80)
        print("🎓 Agent KHU 평가 결과 보고서")
        print("=" * 80)
        
        meta = metrics.get("metadata", {})
        print(f"\n📊 기본 정보")
        print(f"   샘플 수: {meta.get('total_samples', 'N/A')}")
        print(f"   데이터 소스: {meta.get('source', 'unknown')}")
        print(f"   생성 시간: {meta.get('timestamp', 'N/A')[:19]}")
        
        # 전체 성공률
        overall = metrics.get("overall", {})
        print(f"\n✅ 전체 성공 지표")
        print(f"   성공률: {overall.get('success_rate', 0)}%")
        print(f"   성공: {overall.get('success_count', 0)} / {overall.get('total', 0)}")
        print(f"   실패: {overall.get('failed_count', 0)}")
        
        # 지연
        latency = metrics.get("latency", {})
        print(f"\n⏱️  응답 지연 (성공한 요청)")
        print(f"   최소: {latency.get('min_ms', 0):>6.0f}ms")
        print(f"   P50 : {latency.get('p50_ms', 0):>6.2f}ms")
        print(f"   P95 : {latency.get('p95_ms', 0):>6.2f}ms")
        print(f"   P99 : {latency.get('p99_ms', 0):>6.2f}ms")
        print(f"   최대: {latency.get('max_ms', 0):>6.0f}ms")
        print(f"   평균: {latency.get('avg_ms', 0):>6.2f}ms (σ={latency.get('stdev_ms', 0):.2f})")
        
        # Tool 사용
        tools = metrics.get("tools", {})
        print(f"\n🔧 Tool 사용 현황")
        print(f"   평균 Tool/요청: {tools.get('avg_tools_per_request', 0):.2f}")
        print(f"   0회 반복: {tools.get('zero_tool_requests', 0)} ({tools.get('zero_tool_rate', 0)}%)")
        print(f"   최대 Tool 수: {tools.get('max_tools', 0)}")
        
        most_used = tools.get("most_used_tools", {})
        if most_used:
            print(f"   상위 도구:")
            for tool, count in list(most_used.items())[:3]:
                print(f"      - {tool}: {count}회")
        
        # 라우팅
        routing = metrics.get("routing", {})
        print(f"\n🛣️  라우팅 결정 분포")
        dist = routing.get("distribution", {})
        for decision, percentage in dist.items():
            print(f"   {decision}: {percentage}%")
        
        # 도메인별 성공률
        by_domain = metrics.get("by_domain", {})
        if by_domain:
            print(f"\n📈 도메인별 성능")
            print(f"   {'도메인':<15} {'성공률':<10} {'P50':<10} {'P95':<10} {'샘플':<8}")
            print(f"   {'-'*53}")
            for domain, stats in sorted(by_domain.items()):
                success_rate = stats.get("success_rate", 0)
                p50 = stats.get("p50_latency_ms", 0)
                p95 = stats.get("p95_latency_ms", 0)
                total = stats.get("total", 0)
                print(f"   {domain:<15} {success_rate:>6.1f}%   {p50:>7.1f}ms  {p95:>7.1f}ms  {total:>5d}")
        
        print("\n" + "=" * 80)
    
    def save_report(self, metrics: Dict, output_file: Path):
        """보고서를 JSON으로 저장"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON 보고서 저장: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Agent KHU 평가 분석")
    parser.add_argument("--es_url", type=str, default="http://localhost:9200", help="Elasticsearch URL")
    parser.add_argument("--input", type=str, help="로컬 평가 결과 JSON 파일")
    parser.add_argument("--output", type=str, default=None, help="분석 결과 저장 경로")
    args = parser.parse_args()
    
    # 로컬 결과 로드 (있으면)
    raw_results = []
    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            with open(input_path) as f:
                raw_results = json.load(f)
            print(f"✅ 로컬 결과 로드: {input_path} ({len(raw_results)}개)")
    
    # 분석 실행
    analyzer = MetricsAnalyzer(es_url=args.es_url, raw_results=raw_results)
    metrics = analyzer.analyze()
    
    if not metrics:
        print("❌ 분석 실패")
        sys.exit(1)
    
    # 보고서 출력
    analyzer.print_report(metrics)
    
    # 저장
    output_file = Path(args.output) if args.output else Path(__file__).parent / "evaluation_metrics.json"
    analyzer.save_report(metrics, output_file)
    
    print(f"\n✨ 분석 완료!")


if __name__ == "__main__":
    main()
