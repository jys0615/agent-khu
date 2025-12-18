from pathlib import Path
from typing import Dict, Any
import os
import sys

# 현재 디렉토리를 sys.path에 추가
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

# Reuse existing scraper functions from local module
try:
    # 패키지 형태: .scrapers.meal_scraper
    from .scrapers.meal_scraper import get_today_meal_with_vision, get_cafeteria_info, scrape_weekly_meal
except Exception:
    try:
        # 패키지 형태: .scraper
        from .scraper import get_today_meal_with_vision, get_cafeteria_info, scrape_weekly_meal
    except Exception:
        try:
            # 스크립트 형태: scraper.py
            from scraper import get_today_meal_with_vision, get_cafeteria_info, scrape_weekly_meal
        except Exception:
            # Last resort: import 실패
            get_today_meal_with_vision = None
            get_cafeteria_info = lambda: {"error": "scraper not found"}
            scrape_weekly_meal = None


def _get_api_key() -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key
    env_path = Path(__file__).parents[2] / "backend" / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip()
        except Exception:
            pass
    return None


async def get_today_meal(args: Dict[str, Any]) -> Dict[str, Any]:
    if get_today_meal_with_vision is None:
        return {"error": "scraper not available"}
    api_key = _get_api_key()
    if not api_key:
        return {"error": "API Key 없음", "message": "ANTHROPIC_API_KEY 환경변수를 설정해주세요"}
    meal_type = args.get("meal_type", "lunch")
    return await get_today_meal_with_vision(api_key, meal_type)


def get_cafeteria_info_service() -> Dict[str, Any]:
    return get_cafeteria_info()


async def scrape_weekly_meal_service() -> Dict[str, Any]:
    if scrape_weekly_meal is None:
        return {"error": "scraper not available"}
    api_key = _get_api_key()
    if not api_key:
        return {"error": "API Key 없음", "message": "ANTHROPIC_API_KEY 환경변수를 설정해주세요"}
    return await scrape_weekly_meal(api_key)
