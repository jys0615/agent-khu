"""
Notice crawling utilities (pure functions, no DB side effects).
"""
import time
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import urllib3

# Disable SSL warnings for legacy sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = "Mozilla/5.0"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Connection": "close",
}


def build_view_url(base_url: str, href: str) -> str:
    """Convert javascript:view('123') to actual view.do URL preserving menuNo."""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("javascript:view("):
        m = re.search(r"view\(['\"]?(\d+)['\"]?\)", href)
        board_id = m.group(1) if m else ""
        parsed = urlparse(base_url)
        path = parsed.path.replace("list.do", "view.do")
        qs = parse_qs(parsed.query)
        if board_id:
            qs["boardId"] = [board_id]
        query = urlencode({k: v[0] for k, v in qs.items() if v})
        return urlunparse((parsed.scheme, parsed.netloc, path, "", query, ""))
    return href


def crawl_swedu(limit: int = 20):
    """소프트웨어융합학과 커스텀 게시판 크롤링."""
    url = "http://swcon.khu.ac.kr/post/?mode=list&board_page=1"
    try:
        html = requests.get(url, timeout=30, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(html.text, "html.parser")
        rows = soup.find_all("tr")[:limit]

        posts = []
        for idx, row in enumerate(rows):
            date_cell = row.find("td", class_="mb-hide-mobile")
            date_text = date_cell.get_text(strip=True) if date_cell else ""
            content = row.find("td", class_="text-left")
            if not content:
                continue
            post_item = content.find("a")
            if not post_item or "title" not in post_item.attrs:
                continue

            posts.append({
                "id": f"swedu_{idx}_{int(time.time())}",
                "source": "swedu",
                "title": post_item.attrs.get("title", ""),
                "content": "",
                "url": post_item.attrs.get("href", ""),
                "date": date_text,
                "author": "소프트웨어융합학과",
                "views": 0,
            })

            if len(posts) >= limit:
                break
        return posts
    except Exception:
        return []


def crawl_standard(dept_name: str, base_url: str, source_code: str, limit: int = 20, keyword: str = None, max_pages: int = 3):
    """표준 게시판 크롤링 (페이지네이션 + 키워드 필터 지원)."""
    all_posts = []

    for page in range(1, max_pages + 1):
        try:
            if "?" in base_url:
                url = f"{base_url}&pageIndex={page}" if "pageIndex=" not in base_url else base_url.replace(f"pageIndex={page-1}", f"pageIndex={page}")
            else:
                url = f"{base_url}?pageIndex={page}"

            resp = requests.get(
                url,
                timeout=15,
                verify=False,
                headers={**HEADERS, "Referer": url},
            )
            if resp.apparent_encoding:
                resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.content, "html.parser")

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
            if not rows:
                li_items = soup.select("ul li")
                if li_items:
                    rows = li_items
            if not rows:
                break

            page_posts = []
            for idx, row in enumerate(rows):
                try:
                    cells = row.select("td")
                    if len(cells) == 5:
                        title_elem = cells[2].select_one("a")
                        date_elem = cells[4]
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
                            or (cells[-1] if cells else None)
                        )

                    if not title_elem or not date_elem:
                        continue

                    date_text = date_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    href = build_view_url(url, href)
                    if href and not href.startswith("http"):
                        href = urljoin(url, href)

                    title_text = title_elem.get_text(strip=True)
                    if not title_text:
                        continue

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
                        "views": 0,
                    })

                except Exception:
                    continue

            all_posts.extend(page_posts)
            if len(all_posts) >= limit:
                break

        except Exception:
            break

    return all_posts[:limit]


def crawl_department(dept, limit: int = 20, keyword: str = None, db=None):
    """DB department 레코드를 받아 크롤링 수행."""
    if not dept or not dept.notice_url:
        return []

    if dept.notice_type == "custom":
        return crawl_swedu(limit)

    return crawl_standard(dept.name, dept.notice_url, dept.code, limit, keyword)
