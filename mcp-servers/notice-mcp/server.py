"""
Notice MCP Server - SSL 검증 우회
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# DB 연결
backend_path = os.getenv("BACKEND_PATH", "/app")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app import crud


def build_view_url(base_url: str, href: str) -> str:
    """Convert javascript:view('123') to actual view.do URL preserving menuNo."""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("javascript:view("):
        # Extract boardId safely
        import re
        m = re.search(r"view\(['\"]?(\d+)['\"]?\)", href)
        board_id = m.group(1) if m else ""
        parsed = urlparse(base_url)
        # Replace list.do with view.do
        path = parsed.path.replace("list.do", "view.do")
        qs = parse_qs(parsed.query)
        # Keep menuNo if present
        if board_id:
            qs["boardId"] = [board_id]
        query = urlencode({k: v[0] for k, v in qs.items() if v})
        return urlunparse((parsed.scheme, parsed.netloc, path, "", query, ""))
    return href


def crawl_swedu(limit=20):
    """소프트웨어융합학과"""
    url = "http://swcon.khu.ac.kr/post/?mode=list&board_page=1"
    try:
        html = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(html.text, 'html.parser')
        rows = soup.find_all('tr')[:limit]
        
        posts = []
        for idx, row in enumerate(rows):
            date_cell = row.find('td', class_="mb-hide-mobile")
            date_text = date_cell.get_text(strip=True) if date_cell else ""
            content = row.find('td', class_="text-left")
            if not content:
                continue
            post_item = content.find('a')
            if not post_item or 'title' not in post_item.attrs:
                continue

            posts.append({
                "id": f"swedu_{idx}_{int(time.time())}",
                "source": "swedu",
                "title": post_item.attrs['title'],
                "content": "",
                "url": post_item.attrs.get('href', ''),
                "date": date_text,
                "author": "소프트웨어융합학과",
                "views": 0
            })

            if len(posts) >= limit:
                break
        return posts
    except:
        return []


def crawl_standard(dept_name, base_url, source_code, limit=20, keyword=None, max_pages=3):
    """표준 게시판 - 페이지네이션 + 키워드 필터링 지원"""
    all_posts = []
    
    for page in range(1, max_pages + 1):
        try:
            # URL에 pageIndex 파라미터 추가
            if '?' in base_url:
                url = f"{base_url}&pageIndex={page}" if 'pageIndex=' not in base_url else base_url.replace(f"pageIndex={page-1}", f"pageIndex={page}")
            else:
                url = f"{base_url}?pageIndex={page}"
            
            print(f"  📄 {dept_name} 페이지 {page} 크롤링 중...")
            
            resp = requests.get(
                url,
                timeout=15,
                verify=False,  # SSL 검증 우회
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                    "Referer": url,
                    "Connection": "close",
                }
            )
            status = resp.status_code
            # 인코딩 보정
            if resp.apparent_encoding:
                resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.content, 'html.parser')

            # 기본, 대체 셀렉터 모두 시도
            selectors = [
                "table.board-list tbody tr",
                "tbody tr",
                "#board tbody tr",
                "table tbody tr",
            ]
            rows = []
            for sel in selectors:
                rows = soup.select(sel)
                if rows:
                    break
    
            # ul/li 게시판 형태도 시도
            if not rows:
                li_items = soup.select("ul li")
                if li_items:
                    rows = li_items
    
            if not rows:
                print(f"  ⚠️ 페이지 {page}: 행 없음")
                break
    
            page_posts = []
            for idx, row in enumerate(rows):
                try:
                    # Check cell count to determine structure
                    cells = row.select('td')
                    
                    # ie.khu.ac.kr/ce.khu.ac.kr: 5 cells [분류1] [분류2] [제목+링크] [파일] [날짜]
                    if len(cells) == 5:
                        title_elem = cells[2].select_one("a")
                        date_elem = cells[4]
                    # Standard boards have 3-4 cells
                    else:
                        title_elem = (
                            row.select_one("td.title a")
                            or row.select_one("td.subj a")
                            or row.select_one("td.subject a")
                            or row.select_one("a")
                        )
                        date_elem = (
                            row.select_one("td.date")
                            or row.select_one("td.regdate")
                            or (row.find_all("td")[-1] if row.find_all("td") else None)
                        )
    
                    if not title_elem or not date_elem:
                        continue
    
                    date_text = date_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    href = build_view_url(url, href)
                    if href and not href.startswith('http'):
                        href = urljoin(url, href)
    
                    title_text = title_elem.get_text(strip=True)
                    if not title_text:
                        continue
                    
                    # 키워드 필터링
                    if keyword and keyword.lower() not in title_text.lower():
                        continue
    
                    page_posts.append({
                        "id": f"{source_code}_{page}_{idx}_{int(time.time())}",
                        "source": source_code,
                        "title": title_text,
                        "content": "",
                        "url": href,
                        "date": date_text,
                        "author": dept_name,
                        "views": 0
                    })
    
                except Exception as e:
                    print(f"  ⚠️ 행 파싱 실패: {e}")
                    continue
            
            all_posts.extend(page_posts)
            print(f"  ✅ 페이지 {page}: {len(page_posts)}개 수집 (키워드: {keyword or '전체'})")
            
            # limit 도달 시 중단
            if len(all_posts) >= limit:
                break
        
        except Exception as e:
            print(f"  ❌ 페이지 {page} 크롤링 실패: {e}")
            break
    
    return all_posts[:limit]

def crawl_department(dept_query, limit=20, keyword=None):
    """
    DB 기반 학과별 크롤링
    
    Args:
        dept_query: 학과명 또는 학과코드 (예: "소프트웨어융합학과", "swedu")
        limit: 크롤링 건수
        keyword: 필터링 키워드
    
    Returns:
        공지사항 리스트
    """
    try:
        # DB 연결
        db = SessionLocal()
        
        # 학과 검색: 정확한 이름 또는 코드로 매칭
        dept = db.query(crud.models.Department).filter(
            (crud.models.Department.name == dept_query) |
            (crud.models.Department.code == dept_query)
        ).first()
        
        if not dept:
            print(f"❌ 학과를 찾을 수 없음: {dept_query}")
            db.close()
            return []
        
        # 공지사항 URL이 없으면 스킵
        if not dept.notice_url:
            print(f"⚠️ {dept.name}({dept.code})은 아직 크롤링 설정이 되어있지 않습니다.")
            db.close()
            return []
        
        print(f"📚 {dept.name} ({dept.code}) 크롤링 중...")
        
        # 학과별 크롤링 방식 결정
        if dept.notice_type == "custom":
            # swcon.khu.ac.kr 같은 커스텀 게시판
            posts = crawl_swedu(limit)
        else:
            # 표준 게시판 형식
            posts = crawl_standard(dept.name, dept.notice_url, dept.code, limit, keyword)
        
        db.close()
        return posts
        
    except Exception as e:
        print(f"❌ 크롤링 중 오류: {e}")
        return []


def _readline():
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except:
        return None

def _send(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _result(id_: int, data: Any, is_error: bool = False):
    content = [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
    _send({"jsonrpc": "2.0", "id": id_, "result": {"content": content, "isError": is_error}})


async def tool_get_latest_notices(args: Dict) -> Dict:
    db = SessionLocal()
    try:
        # department: 학과명 또는 학과코드
        department = args.get("department", "소프트웨어융합학과")
        
        # Department 테이블에서 학과 검색
        dept = db.query(crud.models.Department).filter(
            (crud.models.Department.name == department) |
            (crud.models.Department.code == department)
        ).first()
        
        if not dept:
            return {"error": f"학과를 찾을 수 없습니다: {department}"}
        
        # department.code를 source로 사용
        notices = crud.get_latest_notices(db, dept.code, args.get("limit", 5))
        return {"notices": [{"title": n.title, "url": n.url, "date": n.date, "author": n.author, "source": n.source, "views": n.views or 0} for n in notices]}
    finally:
        db.close()


async def tool_search_notices(args: Dict) -> Dict:
    db = SessionLocal()
    try:
        notices = crud.search_notices(db, args.get("query", ""), args.get("limit", 5))
        return {"notices": [{"title": n.title, "url": n.url, "date": n.date, "author": n.author, "source": n.source, "views": n.views or 0} for n in notices]}
    finally:
        db.close()


async def tool_crawl_fresh_notices(args: Dict) -> Dict:
    department = args.get("department", "소프트웨어융합학과")
    keyword = args.get("keyword")  # 키워드 필터링
    posts = crawl_department(department, args.get("limit", 20), keyword)
    
    # 크롤링 실패도 정상 처리 (신규 공지 없음으로 간주)
    if not posts:
        msg = f"{department} 신규 공지 없음" + (f" (키워드: {keyword})" if keyword else "")
        return {"success": True, "department": department, "crawled": 0, "new_count": 0, "message": msg}
    
    db = SessionLocal()
    try:
        new_count = sum(1 for post in posts if crud.create_notice_from_mcp(db, post))
        result = {"success": True, "department": department, "crawled": len(posts), "new_count": new_count}
        if keyword:
            result["keyword"] = keyword
        return result
    finally:
        db.close()


async def main():
    tools = {"get_latest_notices": tool_get_latest_notices, "search_notices": tool_search_notices, "crawl_fresh_notices": tool_crawl_fresh_notices}
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        if msg.get("method") == "initialize":
            _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "notice-mcp", "version": "2.0.0"}}})
        elif msg.get("method") == "tools/list":
            _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": {"tools": [{"name": "get_latest_notices", "description": "학과별 최신 공지 (학과명 또는 코드로 검색: 소프트웨어융합학과, swedu 등)", "inputSchema": {"type": "object", "properties": {"department": {"type": "string"}, "limit": {"type": "integer"}}}}, {"name": "search_notices", "description": "공지사항 검색", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}, {"name": "crawl_fresh_notices", "description": "학과 공지사항 크롤링 (키워드 필터링 지원)", "inputSchema": {"type": "object", "properties": {"department": {"type": "string", "description": "학과명 또는 코드 (예: 산업경영공학과, ime)"}, "limit": {"type": "integer"}, "keyword": {"type": "string", "description": "필터링 키워드 (예: 장학금, 수강신청)"}}}}]}})
        elif msg.get("method") == "tools/call":
            params = msg.get("params", {})
            try:
                result = await tools[params.get("name")](params.get("arguments", {}))
                _result(msg.get("id"), result)
            except Exception as e:
                _result(msg.get("id"), {"error": str(e)}, is_error=True)
        elif "id" in msg:
            _result(msg["id"], {"status": "noop"})
        else:
            continue

if __name__ == "__main__":
    asyncio.run(main())
