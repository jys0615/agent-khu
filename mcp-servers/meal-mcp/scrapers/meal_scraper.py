"""
경희대 학식 메뉴 크롤러
"""
import sys
import json
from playwright.sync_api import sync_playwright
from datetime import datetime
from typing import List, Dict


def scrape_meal(date: str = None) -> List[Dict]:
    """학식 메뉴 크롤링"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 경희대 학식 사이트 접속
            page.goto("https://khudorm.khu.ac.kr/")
            page.wait_for_load_state("networkidle")
            
            meals = []
            
            # 식당별 크롤링
            cafeterias = page.locator(".cafeteria").all()
            
            for cafeteria in cafeterias:
                name = cafeteria.locator(".name").text_content()
                
                # 조/중/석식
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    menu_elem = cafeteria.locator(f".{meal_type}")
                    
                    if menu_elem.count() > 0:
                        menu = menu_elem.text_content()
                        price_elem = cafeteria.locator(f".{meal_type}-price")
                        price = int(price_elem.text_content().replace(",", "").replace("원", "")) if price_elem.count() > 0 else 0
                        
                        meals.append({
                            "cafeteria": name,
                            "meal_type": meal_type,
                            "date": date,
                            "menu": menu,
                            "price": price
                        })
            
            return meals
        
        finally:
            browser.close()


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else None
    meals = scrape_meal(date)
    print(json.dumps(meals, ensure_ascii=False, indent=2))