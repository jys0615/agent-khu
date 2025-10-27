"""
경희대 수강신청 시스템 크롤러
"""
import sys
import json
from playwright.sync_api import sync_playwright
from typing import List, Dict


def scrape_courses(year: int = 2025, semester: str = "1학기") -> List[Dict]:
    """수강신청 정보 크롤링"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 경희대 수강신청 시스템
            page.goto("https://sugang.khu.ac.kr")
            page.wait_for_load_state("networkidle")
            
            # 년도/학기 선택
            page.select_option('select[name="year"]', str(year))
            page.select_option('select[name="semester"]', semester)
            
            # 학과 선택 (소프트웨어융합대학)
            page.select_option('select[name="college"]', "소프트웨어융합대학")
            page.click('button:has-text("조회")')
            page.wait_for_load_state("networkidle")
            
            courses = []
            
            # 테이블 파싱
            rows = page.locator("table tbody tr").all()
            
            for row in rows:
                try:
                    cells = row.locator("td").all()
                    
                    if len(cells) < 10:
                        continue
                    
                    course = {
                        "year": year,
                        "semester": semester,
                        "course_code": cells[0].text_content().strip(),
                        "course_name": cells[2].text_content().strip(),
                        "professor": cells[5].text_content().strip(),
                        "department": cells[3].text_content().strip(),
                        "credits": int(cells[6].text_content().strip()),
                        "capacity": int(cells[4].text_content().strip()) if cells[4].text_content().strip().isdigit() else 0,
                        "class_time": cells[7].text_content().strip(),
                        "classroom": cells[8].text_content().strip(),
                        "classification": cells[9].text_content().strip(),
                        "language": cells[10].text_content().strip() if len(cells) > 10 else "한국어",
                        "note": cells[11].text_content().strip() if len(cells) > 11 else ""
                    }
                    
                    courses.append(course)
                
                except Exception as e:
                    print(f"Row parsing error: {e}", file=sys.stderr)
                    continue
            
            return courses
        
        except Exception as e:
            print(f"크롤링 에러: {e}", file=sys.stderr)
            return []
        
        finally:
            browser.close()


if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    semester = sys.argv[2] if len(sys.argv) > 2 else "1학기"
    
    courses = scrape_courses(year, semester)
    print(json.dumps(courses, ensure_ascii=False, indent=2))