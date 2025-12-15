"""
Meal Scraper - Playwright + Claude Vision API
식단표 이미지를 읽어서 오늘 메뉴 추출
주간 캐싱 시스템 + Vision 정확도 개선
"""
from playwright.async_api import async_playwright
from anthropic import Anthropic
from datetime import datetime, timedelta
import base64
import asyncio
import json
import os
from pathlib import Path


from pathlib import Path


# 캐시 파일 경로
CACHE_FILE = Path(__file__).parent / "weekly_meal_cache.json"


def load_cache() -> dict:
    """주간 캐시 로드"""
    if not CACHE_FILE.exists():
        return {}
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  캐시 로드 실패: {e}")
        return {}


def save_cache(data: dict):
    """주간 캐시 저장"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 캐시 저장 완료: {CACHE_FILE}")
    except Exception as e:
        print(f"⚠️  캐시 저장 실패: {e}")


def is_cache_valid(cache: dict) -> bool:
    """캐시 유효성 검사 (같은 주간인지 확인)"""
    if not cache or "created_at" not in cache:
        return False
    
    try:
        cached_date = datetime.fromisoformat(cache["created_at"])
        today = datetime.now()
        
        # 월요일 기준으로 주차 계산 (날짜만 비교)
        def get_monday(dt):
            monday = dt - timedelta(days=dt.weekday())
            return monday.date()  # datetime -> date 변환
        
        cached_monday = get_monday(cached_date)
        current_monday = get_monday(today)
        
        is_valid = cached_monday == current_monday
        if not is_valid:
            print(f"🔍 캐시 만료: cached_monday={cached_monday}, current_monday={current_monday}")
        
        return is_valid
    except Exception as e:
        print(f"⚠️  캐시 유효성 검사 실패: {e}")
        return False


def get_from_cache(date_str: str, meal_type: str) -> dict:
    """캐시에서 특정 날짜의 메뉴 조회"""
    cache = load_cache()
    
    if not is_cache_valid(cache):
        print("📭 캐시가 만료되었거나 없습니다")
        return None
    
    weekly_data = cache.get("weekly_data", {})
    if date_str in weekly_data and meal_type in weekly_data[date_str]:
        print(f"✅ 캐시 hit: {date_str} {meal_type}")
        return weekly_data[date_str][meal_type]
    
    print(f"📭 캐시 miss: {date_str} {meal_type}")
    return None


async def scrape_weekly_meal(anthropic_api_key: str) -> dict:
    """
    주간 식단표 전체 스크래핑 (Vision API 1회 호출)
    월요일 ~ 금요일, 중식 + 석식 데이터 추출
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. 페이지 접속
            await page.goto("https://khucoop.com/35", timeout=15000)
            await asyncio.sleep(3)
            
            # 2. 테이블 영역만 크롭 (정확도 향상)
            # 전체 페이지 대신 식단표 테이블만 캡처
            table_selector = "table"  # 실제 selector는 페이지 구조에 따라 조정 필요
            
            try:
                element = await page.query_selector(table_selector)
                if element:
                    screenshot = await element.screenshot(scale="device")
                else:
                    # fallback: 전체 페이지
                    screenshot = await page.screenshot(full_page=True, scale="device")
            except:
                screenshot = await page.screenshot(full_page=True, scale="device")
            
            await browser.close()
            
            # 3. 이번 주 월요일 날짜 계산
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            
            # 4. Vision API로 전체 주간 데이터 추출 (Opus 4.5 - 최고 정확도)
            client = Anthropic(api_key=anthropic_api_key)
            
            message = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4096,
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
                            "text": f"""이 이미지는 경희대학교 국제캠퍼스 학생회관식당 주간메뉴표입니다.

**이번 주 월요일: {monday.strftime('%Y-%m-%d')}**

**⚠️ 중요: 교직원식당(7,500원)은 무시하고, 학생식당만 추출하세요!**

**테이블 행 구조 (위→아래):**
1. 🚫 교직원식당 (7,500원, "구성원앱 결제시 7,000원") - ❌ 이 행은 무시!
2. 🚫 학생식당 조식 (08:30-10:00, 경회인1,000/외부인5,000) - ❌ 이 행도 무시!
3. ✅ 학생식당 중식 던던(A) - 🎯 이 행에서 추출!
4. ✅ 학생식당 중식 우아(B) - 🎯 또는 이 행!
5. ✅ 학생식당 중식 푸짐(C) - 🎯 또는 이 행!
6. ✅ 학생식당 석식 (17:00-18:30) - 🎯 석식은 이 행!

**추출 규칙:**
- 중식: "학생식당" 행 중 "던던(A)" 또는 "우아(B)" 또는 "푸짐(C)" 행의 메뉴
- 석식: "학생식당 (17:00-18:30)" 행의 메뉴
- 가격: 5,000원 (외부인 기준)
- "석식 미운영" 표시 → dinner.available = false

**예시 (12월 15일 월요일 기준):**
- 던던(A) 행 월요일: 깻잎제육덮밥
- 우아(B) 행 월요일: 돈까스마요덮밥
- 푸짐(C) 행 월요일: 치즈불닭
→ 이 중 하나를 lunch.menu로 사용

**메뉴명 추출 시:**
- 첫 줄의 대표 메뉴명만 (예: "깻잎제육덮밥")
- 원산지 정보(돼지:국내산) 제외
- 반찬류(배추김치, 깍두기) 제외
- 빨간 도시락 아이콘이 있는 메뉴 우선

**JSON 형식:**
```json
{{
  "monday": {{
    "date": "{(monday).strftime('%Y-%m-%d')}",
    "day": "월요일",
    "lunch": {{ "menu": "깻잎제육덮밥", "price": 5000, "available": true }},
    "dinner": {{ "menu": "돈육낙지덮밥", "price": 5000, "available": true }}
  }},
  "tuesday": {{
    "date": "{(monday + timedelta(days=1)).strftime('%Y-%m-%d')}",
    "day": "화요일",
    "lunch": {{ "menu": "...", "price": 5000, "available": true }},
    "dinner": {{ "menu": "...", "price": 5000, "available": true }}
  }},
  "wednesday": {{
    "date": "{(monday + timedelta(days=2)).strftime('%Y-%m-%d')}",
    "day": "수요일",
    "lunch": {{ "menu": "...", "price": 5000, "available": true }},
    "dinner": {{ "menu": "...", "price": 5000, "available": true }}
  }},
  "thursday": {{
    "date": "{(monday + timedelta(days=3)).strftime('%Y-%m-%d')}",
    "day": "목요일",
    "lunch": {{ "menu": "...", "price": 5000, "available": true }},
    "dinner": {{ "menu": null, "price": null, "available": false }}
  }},
  "friday": {{
    "date": "{(monday + timedelta(days=4)).strftime('%Y-%m-%d')}",
    "day": "금요일",
    "lunch": {{ "menu": "...", "price": 5000, "available": true }},
    "dinner": {{ "menu": null, "price": null, "available": false }}
  }}
}}
```

**JSON만 반환하세요.**"""
                        }
                    ]
                }]
            )
            
            # 5. 응답 파싱
            response_text = message.content[0].text
            
            # JSON 추출
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            weekly_data = json.loads(response_text)
            
            # 6. 캐시 구조로 변환 (날짜 기준 인덱싱)
            cache_structure = {
                "created_at": datetime.now().isoformat(),
                "week_start": monday.strftime('%Y-%m-%d'),
                "weekly_data": {}
            }
            
            day_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4
            }
            
            for day_en, offset in day_map.items():
                if day_en in weekly_data:
                    date_str = (monday + timedelta(days=offset)).strftime('%Y-%m-%d')
                    day_data = weekly_data[day_en]
                    
                    cache_structure["weekly_data"][date_str] = {
                        "lunch": {
                            "date": date_str,
                            "day": day_data.get("day", ""),
                            "meal_type": "lunch",
                            **day_data.get("lunch", {})
                        },
                        "dinner": {
                            "date": date_str,
                            "day": day_data.get("day", ""),
                            "meal_type": "dinner",
                            **day_data.get("dinner", {})
                        }
                    }
            
            # 7. 캐시 저장
            save_cache(cache_structure)
            
            return {
                "success": True,
                "message": "주간 식단표 스크래핑 완료",
                "week_start": monday.strftime('%Y-%m-%d'),
                "cached_days": len(cache_structure["weekly_data"])
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            try:
                await browser.close()
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "message": "주간 식단표 스크래핑 실패"
            }


async def get_today_meal_with_vision(anthropic_api_key: str, meal_type: str = "lunch") -> dict:
    """
    오늘 식단 조회 (캐시 우선 확인)
    1. 캐시에 있으면 캐시 반환
    2. 없으면 주간 스크래핑 실행 후 캐시 반환
    """
    
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    # 1. 캐시 확인
    cached_meal = get_from_cache(date_str, meal_type)
    if cached_meal:
        return {
            "success": True,
            "cafeteria": "학생회관 학생식당",
            "location": "학생회관 1층",
            "hours": get_meal_hours(meal_type),
            "menu_url": "https://khucoop.com/35",
            "source_url": "https://khucoop.com/35",
            "from_cache": True,
            **cached_meal
        }
    
    # 2. 캐시 없음 → 주간 스크래핑 실행
    print("📥 캐시 없음. 주간 식단표 스크래핑 시작...")
    scrape_result = await scrape_weekly_meal(anthropic_api_key)
    
    if not scrape_result.get("success"):
        return {
            "error": scrape_result.get("error"),
            "message": "식단 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        }
    
    # 3. 스크래핑 후 다시 캐시에서 조회
    cached_meal = get_from_cache(date_str, meal_type)
    if cached_meal:
        return {
            "success": True,
            "cafeteria": "학생회관 학생식당",
            "location": "학생회관 1층",
            "hours": get_meal_hours(meal_type),
            "menu_url": "https://khucoop.com/35",
            "source_url": "https://khucoop.com/35",
            "from_cache": False,
            "scraping_completed": True,
            **cached_meal
        }
    
    # 4. 스크래핑 후에도 데이터 없음 (주말/공휴일)
    day_of_week = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][today.weekday()]
    
    return {
        "success": True,
        "date": date_str,
        "day": day_of_week,
        "meal_type": meal_type,
        "menu": None,
        "price": None,
        "available": False,
        "message": f"오늘({day_of_week})은 {'중식' if meal_type == 'lunch' else '석식'}이 제공되지 않습니다",
        "cafeteria": "학생회관 학생식당",
        "location": "학생회관 1층",
        "hours": get_meal_hours(meal_type),
        "menu_url": "https://khucoop.com/35",
        "source_url": "https://khucoop.com/35"
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
    
    print("=" * 60)
    print("🧪 Meal MCP Scraper 테스트")
    print("=" * 60)
    
    # 1. 주간 스크래핑 테스트
    print("\n[1] 주간 식단표 스크래핑...")
    scrape_result = await scrape_weekly_meal(api_key)
    
    if scrape_result.get("success"):
        print(f"✅ 주간 스크래핑 성공!")
        print(f"   주간 시작: {scrape_result.get('week_start')}")
        print(f"   캐시된 일수: {scrape_result.get('cached_days')}일")
    else:
        print(f"❌ 실패: {scrape_result.get('message')}")
        return
    
    # 2. 오늘 중식 조회 (캐시에서)
    print("\n[2] 오늘의 중식 메뉴 조회...")
    lunch_result = await get_today_meal_with_vision(api_key, "lunch")
    
    if lunch_result.get("success"):
        print("✅ 성공!")
        print(f"   📅 날짜: {lunch_result.get('date')} {lunch_result.get('day')}")
        print(f"   🍽️  메뉴: {lunch_result.get('menu')}")
        print(f"   💰 가격: {lunch_result.get('price')}원")
        print(f"   📍 위치: {lunch_result.get('location')}")
        print(f"   🔄 캐시 사용: {lunch_result.get('from_cache', False)}")
    else:
        print(f"⚠️  메뉴 없음: {lunch_result.get('message')}")
    
    # 3. 오늘 석식 조회 (캐시에서)
    print("\n[3] 오늘의 석식 메뉴 조회...")
    dinner_result = await get_today_meal_with_vision(api_key, "dinner")
    
    if dinner_result.get("success"):
        print("✅ 성공!")
        print(f"   📅 날짜: {dinner_result.get('date')} {dinner_result.get('day')}")
        print(f"   🍽️  메뉴: {dinner_result.get('menu')}")
        print(f"   💰 가격: {dinner_result.get('price')}원")
        print(f"   🔄 캐시 사용: {dinner_result.get('from_cache', False)}")
    else:
        print(f"⚠️  메뉴 없음: {dinner_result.get('message')}")
    
    # 4. 캐시 파일 확인
    print("\n[4] 캐시 파일 확인...")
    if CACHE_FILE.exists():
        cache = load_cache()
        print(f"✅ 캐시 파일 존재: {CACHE_FILE}")
        print(f"   생성 시간: {cache.get('created_at')}")
        print(f"   주간 시작: {cache.get('week_start')}")
        print(f"   캐시된 날짜 수: {len(cache.get('weekly_data', {}))}")
    else:
        print(f"❌ 캐시 파일 없음: {CACHE_FILE}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test())