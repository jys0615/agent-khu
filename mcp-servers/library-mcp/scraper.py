"""
Library Scraper - Playwright 기반 도서관 좌석 크롤링
"""
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Dict, List, Optional, Tuple
import asyncio


async def get_seat_availability(username: str, password: str, campus: str = "seoul") -> Dict:
    """좌석 현황 조회 - Playwright 생명주기 전체 관리"""
    
    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            # 1. 브라우저 시작
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 2. 로그인
            await page.goto("https://lib.khu.ac.kr/login?retUrl=/relation/hodiSSO?", timeout=15000)
            await page.fill("#id", username)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            
            # 3. 리다이렉트 대기
            try:
                await page.wait_for_url("**/libseat.khu.ac.kr/**", timeout=10000)
            except Exception as e:
                current_url = page.url
                if "login" in current_url:
                    return {
                        "error": "로그인 실패",
                        "message": "학번 또는 비밀번호를 확인해주세요."
                    }
                return {
                    "error": str(e),
                    "message": "로그인 중 오류가 발생했습니다."
                }
            
            # 4. 좌석 페이지로 이동
            await page.goto("https://libseat.khu.ac.kr/", timeout=15000)
            await asyncio.sleep(2)
            
            # 5. 테이블 대기
            try:
                await page.wait_for_selector("table tbody tr", timeout=10000)
            except:
                return {
                    "error": "좌석 데이터 없음",
                    "message": "도서관 좌석 페이지에서 데이터를 찾을 수 없습니다."
                }
            
            # 6. 데이터 추출
            seats_data = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const seats = [];
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 4) {
                            const name = cells[0]?.textContent?.trim() || '';
                            const totalText = cells[1]?.textContent?.trim() || '0';
                            const occupiedText = cells[2]?.textContent?.trim() || '0';
                            const availableText = cells[3]?.textContent?.trim() || '0';
                            
                            // 숫자만 추출 (예: "406(410)" -> 406)
                            const extractNumber = (text) => {
                                const match = text.match(/\\d+/);
                                return match ? parseInt(match[0]) : 0;
                            };
                            
                            const total = extractNumber(totalText);
                            const occupied = extractNumber(occupiedText);
                            const available = extractNumber(availableText);
                            
                            // 운영시간
                            let hours = '';
                            if (cells.length >= 5) {
                                hours = cells[4]?.textContent?.trim() || '';
                            }
                            
                            // "합계" 제외
                            if (name && total > 0 && !name.includes('합계')) {
                                seats.push({
                                    name: name,
                                    total: total,
                                    occupied: occupied,
                                    available: available,
                                    occupancy_rate: total > 0 ? Math.round((occupied / total) * 100) : 0,
                                    hours: hours
                                });
                            }
                        }
                    });
                    
                    return seats;
                }
            """)
            
            if not seats_data:
                return {
                    "error": "좌석 데이터가 비어있습니다",
                    "message": "현재 도서관 좌석 정보를 가져올 수 없습니다."
                }
            
            # 7. 전체 합계 계산
            total_seats = sum(s['total'] for s in seats_data)
            total_occupied = sum(s['occupied'] for s in seats_data)
            total_available = sum(s['available'] for s in seats_data)
            
            result = {
                "campus": "서울캠퍼스" if campus == "seoul" else "국제캠퍼스",
                "library": "중앙도서관",
                "total_seats": total_seats,
                "occupied": total_occupied,
                "available": total_available,
                "occupancy_rate": round((total_occupied / total_seats * 100) if total_seats > 0 else 0, 1),
                "floors": seats_data,
                "updated_at": None
            }
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "message": f"좌석 현황 조회 중 오류가 발생했습니다: {str(e)}"
            }
        
        finally:
            # 8. 정리
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except:
                pass


async def reserve_seat(
    username: str,
    password: str,
    room: str,
    seat_number: Optional[str] = None
) -> Dict:
    """좌석 예약"""
    
    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            # 1. 브라우저 시작
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 2. 로그인
            await page.goto("https://lib.khu.ac.kr/login?retUrl=/relation/hodiSSO?", timeout=15000)
            await page.fill("#id", username)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            
            try:
                await page.wait_for_url("**/libseat.khu.ac.kr/**", timeout=10000)
            except:
                return {
                    "error": "로그인 실패",
                    "message": "학번 또는 비밀번호를 확인해주세요."
                }
            
            # 3. 좌석 페이지
            await page.goto("https://libseat.khu.ac.kr/", timeout=15000)
            await asyncio.sleep(2)
            
            # 예약 로직 (구현 필요)
            return {
                "success": False,
                "message": "좌석 예약 기능은 개발 중입니다. 직접 https://libseat.khu.ac.kr/ 에서 예약해주세요.",
                "link": "https://libseat.khu.ac.kr/"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "message": f"좌석 예약 중 오류가 발생했습니다: {str(e)}"
            }
        
        finally:
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except:
                pass


# 테스트용
async def test_login():
    """로그인 테스트"""
    username = input("학번: ")
    password = input("비밀번호: ")
    
    try:
        print("🔄 로그인 중...")
        result = await get_seat_availability(username, password)
        
        if "error" in result:
            print(f"❌ 실패: {result.get('message', result['error'])}")
            return
        
        print("✅ 로그인 성공!")
        print(f"\n📊 {result['library']} 좌석 현황:")
        print(f"   전체: {result['total_seats']}석")
        print(f"   이용 중: {result['occupied']}석")
        print(f"   이용 가능: {result['available']}석")
        print(f"   이용률: {result['occupancy_rate']}%")
        print("\n📍 층별 현황:")
        for floor in result['floors']:
            print(f"   {floor['name']}: {floor['available']}/{floor['total']}석 이용 가능 ({floor['occupancy_rate']}%)")
            if floor['hours']:
                print(f"      운영시간: {floor['hours']}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login())