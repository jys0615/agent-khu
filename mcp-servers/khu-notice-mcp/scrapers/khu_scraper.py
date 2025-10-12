#!/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
"""
KHU Notice Scraper
경희대학교 SW중심대학사업단 공지사항 크롤러
"""

import sys
import json
import hashlib
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup


def scrape_swedu(limit: int = 10) -> List[Dict]:
    """
    SW중심대학사업단 공지사항 크롤링
    """
    url = "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        notices = []
        
        # 게시판 테이블 찾기
        rows = soup.select('table tbody tr')
        
        print(f"Found {len(rows)} rows", file=sys.stderr)
        
        for row in rows[:limit]:
            try:
                # td_subject: 제목
                title_td = row.select_one('td.td_subject')
                if not title_td:
                    continue
                
                # 링크와 제목 추출
                link_tag = title_td.find('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href', '')
                
                if link and not link.startswith('http'):
                    link = f"https://swedu.khu.ac.kr{link}"
                
                # td_name: 작성자
                author_td = row.select_one('td.td_name')
                author = author_td.get_text(strip=True) if author_td else ""
                
                # td_datetime: 날짜
                date_td = row.select_one('td.td_datetime')
                date = ""
                if date_td:
                    # 아이콘 제거하고 텍스트만
                    date = date_td.get_text(strip=True).replace('', '').strip()
                
                # td_num: 조회수
                views_td = row.select_one('td.td_num')
                views = 0
                if views_td:
                    views_text = views_td.get_text(strip=True).replace('', '').strip()
                    try:
                        views = int(views_text)
                    except:
                        views = 0
                
                if not title:
                    continue
                
                # 고유 ID 생성
                notice_id = hashlib.md5(f"swedu_{title}_{date}".encode()).hexdigest()[:16]
                
                notices.append({
                    "id": notice_id,
                    "source": "swedu",
                    "title": title,
                    "content": title,  # 목록에서는 상세 내용 없음
                    "url": link,
                    "date": date,
                    "author": author,
                    "views": views,
                })
                
                print(f"Parsed: {title[:50]}", file=sys.stderr)
                
            except Exception as e:
                print(f"Error parsing row: {e}", file=sys.stderr)
                continue
        
        print(f"Total notices: {len(notices)}", file=sys.stderr)
        return notices
    
    except Exception as e:
        print(f"Error scraping swedu: {str(e)}", file=sys.stderr)
        return []


def scrape_department(limit: int = 10) -> List[Dict]:
    """
    소프트웨어융합학과 공지사항 - 샘플 데이터
    """
    base_date = datetime.now()
    
    sample_notices = [
        {
            "id": hashlib.md5(f"dept_1".encode()).hexdigest()[:16],
            "source": "department",
            "title": "2025-1학기 전공 설명회 개최",
            "content": "신입생 대상 전공 설명회를 개최합니다.",
            "url": "http://cs.khu.ac.kr/cs/user/bbs/BMSR00040/view.do?seq=456",
            "date": "2025-03-15",
        },
        {
            "id": hashlib.md5(f"dept_2".encode()).hexdigest()[:16],
            "source": "department",
            "title": "졸업논문 제출 안내",
            "content": "2024-2학기 졸업 예정자 논문 제출 일정을 안내합니다.",
            "url": "http://cs.khu.ac.kr/cs/user/bbs/BMSR00040/view.do?seq=455",
            "date": "2025-06-01",
        },
        {
            "id": hashlib.md5(f"dept_3".encode()).hexdigest()[:16],
            "source": "department",
            "title": "학과 MT 참가 신청",
            "content": "2025-1학기 학과 MT 참가 신청을 받습니다.",
            "url": "http://cs.khu.ac.kr/cs/user/bbs/BMSR00040/view.do?seq=454",
            "date": "2025-04-10",
        },
    ]
    
    print(f"Generated {len(sample_notices)} department notices", file=sys.stderr)
    return sample_notices[:limit]


def scrape_schedule(limit: int = 50) -> List[Dict]:
    """
    2025학년도 학사일정 샘플 데이터
    """
    schedules = [
        {
            "id": hashlib.md5("schedule_1".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "2025-1학기 개강",
            "content": "2025-03-03: 2025-1학기 개강",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-03-03",
        },
        {
            "id": hashlib.md5("schedule_2".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "수강신청 정정기간",
            "content": "2025-03-03 ~ 2025-03-07: 수강신청 정정기간",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-03-03 ~ 2025-03-07",
        },
        {
            "id": hashlib.md5("schedule_3".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "중간고사 기간",
            "content": "2025-04-21 ~ 2025-04-27: 중간고사 기간",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-04-21 ~ 2025-04-27",
        },
        {
            "id": hashlib.md5("schedule_4".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "1학기 종강",
            "content": "2025-06-13: 1학기 종강",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-06-13",
        },
        {
            "id": hashlib.md5("schedule_5".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "기말고사 기간",
            "content": "2025-06-16 ~ 2025-06-22: 기말고사 기간",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-06-16 ~ 2025-06-22",
        },
        {
            "id": hashlib.md5("schedule_6".encode()).hexdigest()[:16],
            "source": "schedule",
            "title": "하계방학 시작",
            "content": "2025-06-23: 하계방학 시작",
            "url": "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048",
            "date": "2025-06-23",
        },
    ]
    
    print(f"Generated {len(schedules)} schedule items", file=sys.stderr)
    return schedules[:limit]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: khu_scraper.py <source> <limit>", file=sys.stderr)
        print(json.dumps([]), ensure_ascii=False)
        sys.exit(0)
    
    source = sys.argv[1]
    limit = int(sys.argv[2])
    
    notices = []
    
    if source == "swedu":
        notices = scrape_swedu(limit)
    elif source == "department":
        notices = scrape_department(limit)
    elif source == "schedule":
        notices = scrape_schedule(limit)
    else:
        print(f"Unknown source: {source}", file=sys.stderr)
    
    print(json.dumps(notices, ensure_ascii=False, indent=2))