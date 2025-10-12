#!/usr/bin/env python3
"""
KHU Notice Scraper
경희대학교 공지사항 크롤러
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
    url = "https://swedu.khu.ac.kr/swedu/user/bbs/BMSR00013/list.do?menuNo=14400018"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        notices = []
        rows = soup.select('table.board-table tbody tr')[:limit]
        
        for row in rows:
            try:
                # 번호
                num_td = row.select_one('td.text-center')
                if not num_td or num_td.text.strip() in ['공지', '']:
                    continue
                
                # 제목 및 링크
                title_td = row.select_one('td.text-left a')
                if not title_td:
                    continue
                
                title = title_td.text.strip()
                link = title_td.get('href', '')
                
                if link and not link.startswith('http'):
                    link = f"https://swedu.khu.ac.kr{link}"
                
                # 날짜
                date_td = row.select('td.text-center')[-1]
                date = date_td.text.strip() if date_td else ""
                
                # 고유 ID 생성
                notice_id = hashlib.md5(f"swedu_{title}_{date}".encode()).hexdigest()[:16]
                
                notices.append({
                    "id": notice_id,
                    "source": "swedu",
                    "title": title,
                    "content": title,  # 상세 내용은 별도 크롤링 필요
                    "url": link,
                    "date": date,
                })
            except Exception as e:
                print(f"Error parsing row: {e}", file=sys.stderr)
                continue
        
        return notices
    
    except Exception as e:
        print(f"Error scraping swedu: {str(e)}", file=sys.stderr)
        return []


def scrape_department(limit: int = 10) -> List[Dict]:
    """
    소프트웨어융합대학 공지사항 크롤링
    """
    # 소프트웨어융합대학 공지사항 URL (예시)
    # 실제 URL은 확인 필요
    url = "https://software.khu.ac.kr/software/user/bbs/BMSR00040/list.do?menuNo=9900065"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        notices = []
        rows = soup.select('table tbody tr')[:limit]
        
        for row in rows:
            try:
                # 제목
                title_td = row.select_one('td.text-left a, td a')
                if not title_td:
                    continue
                
                title = title_td.text.strip()
                link = title_td.get('href', '')
                
                if link and not link.startswith('http'):
                    link = f"https://software.khu.ac.kr{link}"
                
                # 날짜
                date_tds = row.select('td')
                date = date_tds[-1].text.strip() if len(date_tds) > 0 else ""
                
                # 고유 ID 생성
                notice_id = hashlib.md5(f"department_{title}_{date}".encode()).hexdigest()[:16]
                
                notices.append({
                    "id": notice_id,
                    "source": "department",
                    "title": title,
                    "content": title,
                    "url": link,
                    "date": date,
                })
            except Exception as e:
                print(f"Error parsing row: {e}", file=sys.stderr)
                continue
        
        return notices
    
    except Exception as e:
        print(f"Error scraping department: {str(e)}", file=sys.stderr)
        return []


def scrape_schedule(limit: int = 50) -> List[Dict]:
    """
    학사일정 크롤링
    """
    url = "https://shaksa.khu.ac.kr/shaksa/user/contents/view.do?menuNo=8400048"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        schedules = []
        
        # 표에서 학사일정 추출
        tables = soup.select('table')
        
        for table in tables:
            rows = table.select('tr')
            
            for row in rows:
                cells = row.select('td')
                
                if len(cells) >= 2:
                    try:
                        date = cells[0].text.strip()
                        event = cells[1].text.strip()
                        
                        if not date or not event:
                            continue
                        
                        # 고유 ID 생성
                        schedule_id = hashlib.md5(f"schedule_{date}_{event}".encode()).hexdigest()[:16]
                        
                        schedules.append({
                            "id": schedule_id,
                            "source": "schedule",
                            "title": event,
                            "content": f"{date}: {event}",
                            "url": url,
                            "date": date,
                        })
                    except Exception as e:
                        continue
        
        return schedules[:limit]
    
    except Exception as e:
        print(f"Error scraping schedule: {str(e)}", file=sys.stderr)
        return []


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: khu_scraper.py <source> <limit>", file=sys.stderr)
        sys.exit(1)
    
    source = sys.argv[1]
    limit = int(sys.argv[2])
    
    if source == "swedu":
        notices = scrape_swedu(limit)
    elif source == "department":
        notices = scrape_department(limit)
    elif source == "schedule":
        notices = scrape_schedule(limit)
    else:
        print(f"Unknown source: {source}", file=sys.stderr)
        sys.exit(1)
    
    print(json.dumps(notices, ensure_ascii=False, indent=2))