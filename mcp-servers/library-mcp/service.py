import json
from pathlib import Path
from typing import Dict, Any

try:
    from .scrapers.library_scraper import get_seat_availability, reserve_seat
except Exception:
    get_seat_availability = None
    reserve_seat = None

DATA_PATH = Path(__file__).parent / "data" / "library_info.json"


def load_library_info() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        return {}
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


async def get_seat_availability_service(args: Dict[str, Any]) -> Dict[str, Any]:
    username = args.get("username")
    password = args.get("password")
    campus = args.get("campus", "seoul")
    if not username or not password:
        return {
            "error": "로그인이 필요합니다",
            "required": ["username", "password"],
            "message": "학번과 비밀번호를 입력해주세요",
        }
    if get_seat_availability is None:
        return {"error": "scraper not available"}
    try:
        return await get_seat_availability(username, password, campus)
    except Exception as e:
        return {"error": str(e), "message": "좌석 현황 조회 실패. 로그인 정보를 확인하세요."}


async def reserve_seat_service(args: Dict[str, Any]) -> Dict[str, Any]:
    username = args.get("username")
    password = args.get("password")
    room = args.get("room")
    seat_number = args.get("seat_number")
    if not username or not password:
        return {"error": "로그인이 필요합니다"}
    if not room:
        return {"error": "예약할 열람실을 지정해주세요"}
    if reserve_seat is None:
        return {"error": "scraper not available"}
    try:
        return await reserve_seat(username, password, room, seat_number)
    except Exception as e:
        return {"error": str(e)}
