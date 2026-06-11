"""
Course MCP Server — FastMCP + Streamable HTTP (Phase 2)
종합시간표 자동 크롤링 (Playwright)
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from fastmcp import FastMCP
from playwright.async_api import async_playwright

backend_path = os.getenv("BACKEND_PATH", "/app")
sys.path.insert(0, backend_path)

PORT = int(os.getenv("PORT", "8105"))
mcp = FastMCP("course-mcp")

print("🚀 Course MCP Server 시작", file=sys.stderr)
print("📚 종합시간표 자동 조회 서버", file=sys.stderr)
print("-" * 40, file=sys.stderr)


class CourseScraper:
    """수강신청 사이트 크롤러 (캐시 포함)"""

    BASE_URL = "https://sugang.khu.ac.kr/"
    CACHE_SECONDS = 3600

    def __init__(self) -> None:
        self._cache: Dict[str, tuple] = {}

    async def get_courses(self, department: str = "소프트웨어융합학과", semester: Optional[str] = None) -> List[Dict]:
        key = f"{department}_{semester}"
        if key in self._cache:
            data, ts = self._cache[key]
            if (datetime.now() - ts).seconds < self.CACHE_SECONDS:
                return data

        print(f"🔍 크롤링 시작: {department} - {semester or '현재학기'}", file=sys.stderr)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(self.BASE_URL, wait_until="networkidle")
                await page.click("text=종합시간표")
                await page.wait_for_load_state("networkidle")
                await page.select_option("select#department", department)
                if semester:
                    await page.select_option("select#semester", semester)
                await page.click("button#search")
                await page.wait_for_selector("table.timetable", timeout=10000)

                courses = await page.evaluate("""
                    () => {
                        const rows = document.querySelectorAll('table.timetable tbody tr');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td');
                            return {
                                code: cells[0]?.textContent?.trim() || '',
                                name: cells[1]?.textContent?.trim() || '',
                                professor: cells[2]?.textContent?.trim() || '',
                                credits: cells[3]?.textContent?.trim() || '',
                                time: cells[4]?.textContent?.trim() || '',
                                room: cells[5]?.textContent?.trim() || '',
                                type: cells[6]?.textContent?.trim() || '',
                                capacity: cells[7]?.textContent?.trim() || '',
                            };
                        }).filter(c => c.code);
                    }
                """)
                self._cache[key] = (courses, datetime.now())
                return courses
            except Exception as e:
                print(f"❌ 크롤링 오류: {e}", file=sys.stderr)
                return []
            finally:
                await browser.close()


_scraper = CourseScraper()


@mcp.tool()
async def search_courses(department: str = "소프트웨어융합학과", keyword: str = "") -> dict:
    """학과별 개설 교과목 자동 조회 (종합시간표 크롤링)

    Args:
        department: 학과명 (예: 소프트웨어융합학과, 컴퓨터공학과)
        keyword: 과목명 또는 교수명 검색어 (비워두면 전체)
    """
    courses = await _scraper.get_courses(department)
    if keyword:
        kw = keyword.lower()
        courses = [
            c for c in courses
            if kw in c.get("name", "").lower()
            or kw in c.get("professor", "").lower()
            or kw in c.get("code", "").lower()
        ]
    return {"department": department, "total": len(courses), "courses": courses[:20]}


@mcp.tool()
async def get_professor_courses(professor: str) -> dict:
    """특정 교수의 담당 과목 조회

    Args:
        professor: 교수명
    """
    all_courses = await _scraper.get_courses()
    courses = [c for c in all_courses if professor in c.get("professor", "")]
    return {"professor": professor, "total": len(courses), "courses": courses}


@mcp.tool()
async def get_course_by_code(code: str) -> dict:
    """과목 코드로 상세 정보 조회

    Args:
        code: 과목 코드
    """
    all_courses = await _scraper.get_courses()
    course = next((c for c in all_courses if c.get("code") == code), None)
    if course:
        return {"found": True, "course": course}
    return {"found": False, "error": f"과목 코드 {code}를 찾을 수 없습니다"}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
