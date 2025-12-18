"""
경희대 도서관 좌석 현황 크롤러 (비공식)
"""
import sys
import json
from typing import List, Dict
from playwright.async_api import async_playwright


async def get_seat_availability(username: str, password: str, campus: str = "global") -> Dict:
    """로그인 후 열람실 좌석 현황을 크롤링.

    주의: 사이트 구조가 바뀌면 선택자를 업데이트해야 합니다.
    실패 시 최소한의 안내 메시지와 빈 좌석 목록을 반환합니다.
    """

    url = "https://library.khu.ac.kr/seat"
    seats: List[Dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")

            # 로그인 시도 (사이트 구조에 따라 selector 수정 필요)
            try:
                await page.fill("input[name='id']", username)
                await page.fill("input[name='password']", password)
                # 로그인 버튼 추정 선택자
                await page.click("button[type='submit'], button.login, input[type='submit']")
                await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"⚠️ 로그인 단계 스킵/실패: {e}", file=sys.stderr)

            # 열람실 카드 파싱 (구조 추정)
            rooms = await page.query_selector_all(".room-item, .reading-room, .seat-room")
            for room in rooms:
                try:
                    location = (await room.query_selector(".room-name, .name, .title")).inner_text().strip()
                    floor_el = await room.query_selector(".floor")
                    floor = (await floor_el.inner_text()).strip() if floor_el else None
                    total_text_el = await room.query_selector(".total-seats, .total")
                    avail_text_el = await room.query_selector(".available-seats, .available")
                    total = int((await total_text_el.inner_text()).replace("석", "").strip()) if total_text_el else 0
                    available = int((await avail_text_el.inner_text()).replace("석", "").strip()) if avail_text_el else 0
                    seats.append({
                        "location": location,
                        "floor": floor,
                        "total_seats": total,
                        "available_seats": available
                    })
                except Exception as inner_e:
                    print(f"⚠️ 열람실 파싱 실패: {inner_e}", file=sys.stderr)

            return {
                "campus": campus,
                "source": url,
                "seats": seats,
                "success": True,
                "message": "실시간 좌석 현황" if seats else "좌석 정보를 찾지 못했습니다."
            }
        except Exception as e:
            print(f"크롤링 에러: {e}", file=sys.stderr)
            return {
                "campus": campus,
                "source": url,
                "seats": [],
                "success": False,
                "message": "좌석 현황을 불러오지 못했습니다."
            }
        finally:
            await browser.close()


async def reserve_seat(username: str, password: str, room: str, seat_number: str | None = None) -> Dict:
    # 예약 로직 미구현: 자리 잡아둘 수 있도록 안내만 반환
    return {
        "success": False,
        "message": "자동 좌석 예약은 아직 지원하지 않습니다. 웹 포털에서 직접 예약해주세요.",
        "room": room,
        "seat_number": seat_number,
    }


if __name__ == "__main__":
    import asyncio
    async def _test():
        data = await get_seat_availability("demo", "demo")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    asyncio.run(_test())