from playwright.async_api import async_playwright

async def get_courses():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 메인 페이지 로드
        await page.goto("https://sugang.khu.ac.kr/")
        
        # iframe 대기
        await page.wait_for_selector("#Main")
        
        # "종합시간표 조회" 클릭
        await page.click("text=종합시간표 조회")
        
        # 데이터 로드 대기
        await page.wait_for_timeout(2000)
        
        # JSON 데이터 추출
        courses = await page.evaluate("""
            () => {
                // JavaScript로 데이터 추출
                return window.courseData || [];
            }
        """)
        
        return courses
    
if __name__ == "__main__":
    import asyncio
    courses = asyncio.run(get_courses())
    for course in courses:
        print(course)