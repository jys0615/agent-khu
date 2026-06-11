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
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = await browser.new_page()
            try:
                await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=20000)

                # 학과/학년 선택 후 검색
                await page.wait_for_selector("select", timeout=10000)
                selects = await page.query_selector_all("select")
                if selects:
                    # 첫 번째 select에 학과명 시도
                    try:
                        await selects[0].select_option(label=department)
                    except Exception:
                        pass
                    if semester and len(selects) > 1:
                        try:
                            await selects[1].select_option(label=semester)
                        except Exception:
                            pass

                # 검색 버튼 클릭 시도
                for btn_sel in ["button[type='submit']", "input[type='submit']", "button.search", "button:has-text('검색')"]:
                    try:
                        btn = await page.query_selector(btn_sel)
                        if btn:
                            await btn.click()
                            break
                    except Exception:
                        continue

                # 결과 테이블 대기
                await page.wait_for_selector("table", timeout=10000)

                courses = await page.evaluate("""
                    () => {
                        const tables = document.querySelectorAll('table');
                        let bestTable = null;
                        let maxRows = 0;
                        for (const t of tables) {
                            const rows = t.querySelectorAll('tbody tr');
                            if (rows.length > maxRows) {
                                maxRows = rows.length;
                                bestTable = t;
                            }
                        }
                        if (!bestTable) return [];
                        const rows = bestTable.querySelectorAll('tbody tr');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length < 3) return null;
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
                        }).filter(c => c && c.code);
                    }
                """)
                self._cache[key] = (courses, datetime.now())
                print(f"✅ 크롤링 완료: {len(courses)}개 과목", file=sys.stderr)
                return courses
            except Exception as e:
                print(f"❌ 크롤링 오류: {e}", file=sys.stderr)
                return []
            finally:
                await browser.close()


_scraper = CourseScraper()


_FALLBACK = {
    "available": False,
    "message": "종합시간표 크롤링에 실패했습니다. 아래 공식 사이트에서 직접 확인해주세요.",
    "official_url": "https://sugang.khu.ac.kr/",
    "courses": [],
}


@mcp.tool()
async def search_courses(department: str = "소프트웨어융합학과", keyword: str = "") -> dict:
    """학과별 개설 교과목 자동 조회 (종합시간표 크롤링)

    Args:
        department: 학과명 (예: 소프트웨어융합학과, 컴퓨터공학과)
        keyword: 과목명 또는 교수명 검색어 (비워두면 전체)
    """
    courses = await _scraper.get_courses(department)
    if not courses:
        return {**_FALLBACK, "department": department, "total": 0}
    if keyword:
        kw = keyword.lower()
        courses = [
            c for c in courses
            if kw in c.get("name", "").lower()
            or kw in c.get("professor", "").lower()
            or kw in c.get("code", "").lower()
        ]
    return {"available": True, "department": department, "total": len(courses), "courses": courses[:20]}


@mcp.tool()
async def get_professor_courses(professor: str) -> dict:
    """특정 교수의 담당 과목 조회

    Args:
        professor: 교수명
    """
    all_courses = await _scraper.get_courses()
    if not all_courses:
        return {**_FALLBACK, "professor": professor}
    courses = [c for c in all_courses if professor in c.get("professor", "")]
    return {"available": True, "professor": professor, "total": len(courses), "courses": courses}


@mcp.tool()
async def get_course_by_code(code: str) -> dict:
    """과목 코드로 상세 정보 조회

    Args:
        code: 과목 코드
    """
    all_courses = await _scraper.get_courses()
    if not all_courses:
        return {**_FALLBACK, "code": code}
    course = next((c for c in all_courses if c.get("code") == code), None)
    if course:
        return {"found": True, "course": course}
    return {"found": False, "error": f"과목 코드 {code}를 찾을 수 없습니다", "official_url": "https://sugang.khu.ac.kr/"}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
