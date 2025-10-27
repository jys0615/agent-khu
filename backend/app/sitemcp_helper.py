"""
sitemcp 헬퍼 함수들
"""
import subprocess
import json
from typing import List, Dict, Any


def search_khu_site(site_url: str, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
    """
    sitemcp로 경희대 사이트 검색 (동기 버전)
    """
    import os
    sitemcp_path = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/sitemcp/dist/cli.mjs")
    
    try:
        # sitemcp 실행하여 사이트 크롤링
        # 타임아웃 60초로 증가, 캐시 활성화
        result = subprocess.run(
            [
                "node",
                sitemcp_path,
                site_url,
                "--concurrency", "10",  # 동시 요청 증가
                "--limit", str(max_results),
                "--max-length", "1000",  # 길이 줄임
                "--cache"  # 캐시 활성화
            ],
            capture_output=True,
            text=True,
            timeout=60  # 60초로 증가
        )
        
        if result.returncode != 0:
            print(f"sitemcp stderr: {result.stderr}")
            # stderr 출력해도 계속 진행
        
        # stdout 확인
        if not result.stdout.strip():
            print("sitemcp 출력 없음")
            return []
        
        print(f"sitemcp raw output:\n{result.stdout[:500]}")  # 디버깅용
        
        # JSON 파싱 시도
        lines = result.stdout.strip().split('\n')
        results = []
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                
                # 다양한 응답 형식 처리
                if isinstance(data, dict):
                    # MCP 응답
                    if "result" in data:
                        content = data["result"].get("content", [])
                        for item in content:
                            if isinstance(item, dict):
                                results.append({
                                    "title": item.get("title", item.get("text", "")[:100]),
                                    "url": item.get("url", site_url),
                                    "content": item.get("text", item.get("content", ""))[:500]
                                })
                    
                    # 직접 데이터
                    elif "title" in data or "text" in data:
                        results.append({
                            "title": data.get("title", data.get("text", "")[:100]),
                            "url": data.get("url", site_url),
                            "content": data.get("content", data.get("text", ""))[:500]
                        })
                        
            except json.JSONDecodeError as e:
                # JSON이 아닌 일반 텍스트
                if len(line) > 20:  # 의미 있는 텍스트만
                    results.append({
                        "title": line[:100],
                        "url": site_url,
                        "content": line[:500]
                    })
        
        # query로 필터링
        if query and results:
            results = [
                r for r in results 
                if query.lower() in json.dumps(r, ensure_ascii=False).lower()
            ]
        
        print(f"sitemcp 결과: {len(results)}개")
        return results[:max_results]
    
    except subprocess.TimeoutExpired:
        print(f"sitemcp 타임아웃 (60초 초과)")
        return []
    except Exception as e:
        print(f"sitemcp 에러: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_latest_from_khu(site_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    경희대 사이트에서 최신 콘텐츠 가져오기
    """
    sites = {
        "swedu": "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01",
        "cs": "https://ce.khu.ac.kr/ce/notice/notice.do",
        "library": "https://library.khu.ac.kr",
        "dorm": "https://khudorm.khu.ac.kr"
    }
    
    site_url = sites.get(site_name)
    
    if not site_url:
        return []
    
    return search_khu_site(site_url, "", limit)