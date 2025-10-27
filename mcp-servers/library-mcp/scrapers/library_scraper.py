"""
경희대 도서관 좌석 현황 크롤러
"""
import sys
import json
from playwright.sync_api import sync_playwright
from typing import List, Dict


def scrape_library_seats() -> List[Dict]:
    """도서관 좌석 현황 크롤링"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 경희대 도서관 좌석 예약 시스템
            # URL은 실제 경희대 시스템에 맞게 수정 필요
            page.goto("https://library.khu.ac.kr/seat")
            page.wait_for_load_state("networkidle")
            
            seats = []
            
            # 열람실별 크롤링
            rooms = page.locator(".room-item").all()
            
            for room in rooms:
                location = room.locator(".room-name").text_content().strip()
                floor = room.locator(".floor").text_content().strip() if room.locator(".floor").count() > 0 else None
                
                total_text = room.locator(".total-seats").text_content()
                available_text = room.locator(".available-seats").text_content()
                
                total = int(total_text.replace("석", "").strip())
                available = int(available_text.replace("석", "").strip())
                
                seats.append({
                    "location": location,
                    "floor": floor,
                    "total_seats": total,
                    "available_seats": available
                })
            
            return seats
        
        except Exception as e:
            print(f"크롤링 에러: {e}", file=sys.stderr)
            return []
        
        finally:
            browser.close()


if __name__ == "__main__":
    seats = scrape_library_seats()
    print(json.dumps(seats, ensure_ascii=False, indent=2))