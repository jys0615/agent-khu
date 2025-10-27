"""
경희대 공지사항 크롤러
"""

import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Any
import time


def setup_driver():
    """Selenium 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_swedu(max_posts: int = 20) -> List[Dict[str, Any]]:
    """SW중심대학사업단 공지사항 크롤링"""
    driver = setup_driver()
    posts = []
    
    try:
        url = "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01"
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "td_subject")))
        
        # 게시글 목록 가져오기
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")[:max_posts]
        
        for idx, row in enumerate(rows):
            try:
                # 제목 링크
                title_elem = row.find_element(By.CSS_SELECTOR, ".td_subject a")
                title = title_elem.text.strip()
                post_url = title_elem.get_attribute("href")
                
                # 날짜
                date_elem = row.find_element(By.CLASS_NAME, "td_datetime")
                date = date_elem.text.strip()
                
                # 작성자
                try:
                    author_elem = row.find_element(By.CLASS_NAME, "td_name")
                    author = author_elem.text.strip()
                except:
                    author = "SW중심대학사업단"
                
                # 조회수
                try:
                    view_elem = row.find_element(By.CSS_SELECTOR, "td:nth-child(4)")
                    views = int(view_elem.text.strip())
                except:
                    views = 0
                
                if title and post_url:
                    posts.append({
                        "id": f"swedu_{idx}_{int(time.time())}",
                        "source": "swedu",
                        "title": title,
                        "content": "",
                        "url": post_url,
                        "date": date,
                        "author": author,
                        "views": views
                    })
                    
            except Exception as e:
                print(f"게시글 파싱 오류: {e}", file=sys.stderr)
                continue
        
    except Exception as e:
        print(f"크롤링 오류: {e}", file=sys.stderr)
    finally:
        driver.quit()
    
    return posts


def scrape_department(max_posts: int = 20) -> List[Dict[str, Any]]:
    """컴퓨터공학부 공지사항 크롤링"""
    driver = setup_driver()
    posts = []
    
    try:
        url = "https://ce.khu.ac.kr/ce/notice/notice.do"
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "board-list")))
        
        rows = driver.find_elements(By.CSS_SELECTOR, ".board-list tbody tr")[:max_posts]
        
        for idx, row in enumerate(rows):
            try:
                title_elem = row.find_element(By.CSS_SELECTOR, ".title a")
                title = title_elem.text.strip()
                post_url = title_elem.get_attribute("href")
                
                if not post_url.startswith("http"):
                    post_url = f"https://ce.khu.ac.kr{post_url}"
                
                date_elem = row.find_element(By.CLASS_NAME, "date")
                date = date_elem.text.strip()
                
                try:
                    author_elem = row.find_element(By.CLASS_NAME, "writer")
                    author = author_elem.text.strip()
                except:
                    author = "컴퓨터공학부"
                
                if title and post_url:
                    posts.append({
                        "id": f"dept_{idx}_{int(time.time())}",
                        "source": "department",
                        "title": title,
                        "content": "",
                        "url": post_url,
                        "date": date,
                        "author": author,
                        "views": 0
                    })
                    
            except Exception as e:
                print(f"게시글 파싱 오류: {e}", file=sys.stderr)
                continue
        
    except Exception as e:
        print(f"크롤링 오류: {e}", file=sys.stderr)
    finally:
        driver.quit()
    
    return posts


def scrape_schedule(max_posts: int = 20) -> List[Dict[str, Any]]:
    """학사일정 크롤링"""
    # TODO: 실제 학사일정 페이지 크롤링 구현
    return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python khu_scraper.py <source> [limit]", file=sys.stderr)
        sys.exit(1)
    
    source = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    if source == "swedu":
        posts = scrape_swedu(limit)
    elif source == "department":
        posts = scrape_department(limit)
    elif source == "schedule":
        posts = scrape_schedule(limit)
    else:
        posts = []
    
    print(json.dumps(posts, ensure_ascii=False, indent=2))