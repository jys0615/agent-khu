"""
경희대 수강신청 사이트 크롤러
"""
import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def crawl_timetable(department: str, semester: str):
    """
    종합시간표 크롤링
    
    Args:
        department: 학과명
        semester: 학기 (예: 2025-2)
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. 메인 페이지 접속
            await page.goto("https://sugang.khu.ac.kr/", wait_until="networkidle")
            
            # 2. 종합시간표 메뉴 클릭 (셀렉터 확인 필요)
            # TODO: 실제 셀렉터로 교체
            # await page.click("selector_for_timetable_menu")
            
            # 3. 학과 선택
            # TODO: 실제 셀렉터로 교체
            # await page.select_option("select[name='department']", department)
            
            # 4. 학기 선택
            # TODO: 실제 셀렉터로 교체
            # await page.select_option("select[name='semester']", semester)
            
            # 5. 조회 버튼 클릭
            # await page.click("button[type='submit']")
            # await page.wait_for_load_state("networkidle")
            
            # 6. 테이블 파싱
            # TODO: 실제 테이블 구조 파악 후 구현
            courses = []
            
            # rows = await page.query_selector_all("table tbody tr")
            # for row in rows:
            #     cols = await row.query_selector_all("td")
            #     if len(cols) >= 7:
            #         course = {
            #             "course_code": await cols[0].inner_text(),
            #             "course_name": await cols[1].inner_text(),
            #             "professor": await cols[2].inner_text(),
            #             "credits": await cols[3].inner_text(),
            #             "schedule": await cols[4].inner_text(),
            #             "classroom": await cols[5].inner_text(),
            #             "course_type": await cols[6].inner_text()
            #         }
            #         courses.append(course)
            
            print(json.dumps(courses, ensure_ascii=False))
            
        except Exception as e:
            print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        
        finally:
            await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sugang_scraper.py <department> <semester>")
        sys.exit(1)
    
    department = sys.argv[1]
    semester = sys.argv[2]
    
    asyncio.run(crawl_timetable(department, semester))