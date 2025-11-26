"""
Meal Scraper - Playwright + Claude Vision API
식단표 이미지를 읽어서 오늘 메뉴 추출
"""
from playwright.async_api import async_playwright
from anthropic import Anthropic
from datetime import datetime
import base64
import asyncio


async def get_today_meal_with_vision(anthropic_api_key: str, meal_type: str = "lunch") -> dict:
    """
    1. Playwright로 식단표 페이지 접속
    2. 스크린샷 캡처
    3. Claude Vision으로 이미지 분석
    4. 오늘 날짜의 메뉴 추출
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. 페이지 접속
            await page.goto("https://khucoop.com/35", timeout=15000)
            
            # 2. 페이지 로딩 대기 (이미지/테이블이 나타날 때까지)
            await asyncio.sleep(3)  # JavaScript 렌더링 여유시간
            
            # 3. 전체 페이지 스크린샷
            screenshot = await page.screenshot(full_page=True)
            
            await browser.close()
            
            # 4. 오늘 날짜 정보
            today = datetime.now()
            day_of_week = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][today.weekday()]
            date_str = today.strftime('%Y년 %m월 %d일')
            
            # 5. Claude Vision API 호출
            client = Anthropic(api_key=anthropic_api_key)
            
            meal_type_kr = "중식(점심)" if meal_type == "lunch" else "석식(저녁)"
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(screenshot).decode()
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""이 이미지는 경희대학교 국제캠퍼스 학생회관 주간 식단표입니다.

**오늘 날짜: {date_str} {day_of_week}**

다음 정보를 JSON 형식으로 정확하게 추출해주세요:

1. 오늘({day_of_week})의 {meal_type_kr} 메뉴
2. 가격 (있다면)

**중요:**
- 정확히 오늘({day_of_week})에 해당하는 메뉴만 추출
- 메뉴가 여러 개면 모두 포함
- 메뉴가 없으면 null 반환

**JSON 형식:**
```json
{{
  "date": "{today.strftime('%Y-%m-%d')}",
  "day": "{day_of_week}",
  "meal_type": "{meal_type}",
  "menu": "메뉴명 (예: 제육볶음정식, 김치찌개정식)",
  "price": 5000,
  "available": true
}}
```

메뉴가 없으면:
```json
{{
  "date": "{today.strftime('%Y-%m-%d')}",
  "day": "{day_of_week}",
  "meal_type": "{meal_type}",
  "menu": null,
  "price": null,
  "available": false,
  "message": "오늘은 {meal_type_kr}이 제공되지 않습니다"
}}
```"""
                        }
                    ]
                }]
            )
            
            # 6. 응답 파싱
            import json
            response_text = message.content[0].text
            
            # JSON 추출 (```json ... ``` 형식 처리)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            meal_data = json.loads(response_text)
            
            # 7. 식당 정보 추가
            return {
                "success": True,
                "cafeteria": "학생회관 학생식당",
                "location": "학생회관 1층",
                "hours": get_meal_hours(meal_type),
                **meal_data
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            try:
                await browser.close()
            except:
                pass
            
            return {
                "error": str(e),
                "message": "식단 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }


def get_meal_hours(meal_type: str) -> dict:
    """식사 시간 정보"""
    hours = {
        "breakfast": {"start": "08:00", "end": "09:30"},
        "lunch": {"start": "11:30", "end": "14:00"},
        "dinner": {"start": "17:00", "end": "18:30"}
    }
    return hours.get(meal_type, hours["lunch"])


def get_cafeteria_info() -> dict:
    """식당 기본 정보"""
    return {
        "cafeteria": "학생회관 학생식당",
        "location": "학생회관 1층",
        "building_code": "STUDENT-HALL-1F",
        "campus": "국제캠퍼스",
        "hours": {
            "breakfast": {"start": "08:00", "end": "09:30", "note": "운영되지 않을 수 있음"},
            "lunch": {"start": "11:30", "end": "14:00"},
            "dinner": {"start": "17:00", "end": "18:30"}
        },
        "price_range": {
            "min": 4500,
            "max": 6000,
            "average": 5000
        },
        "payment_methods": ["경희카드", "신용카드", "체크카드", "현금"],
        "features": [
            "외부인 출입 가능",
            "다양한 메뉴 구성",
            "주간 메뉴표 게시"
        ],
        "menu_url": "https://khucoop.com/35",
        "contact": "02-961-0233"
    }


# 테스트용
async def test():
    """로컬 테스트"""
    import os
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY 환경변수를 설정해주세요")
        return
    
    print("🔄 오늘의 중식 메뉴 조회 중...")
    result = await get_today_meal_with_vision(api_key, "lunch")
    
    if "error" in result:
        print(f"❌ 실패: {result['message']}")
    else:
        print("✅ 성공!")
        print(f"\n📅 날짜: {result.get('date')} {result.get('day')}")
        print(f"🍽️  메뉴: {result.get('menu')}")
        print(f"💰 가격: {result.get('price')}원")
        print(f"📍 위치: {result.get('location')}")
        print(f"⏰ 시간: {result.get('hours')}")


if __name__ == "__main__":
    asyncio.run(test())