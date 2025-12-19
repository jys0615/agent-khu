"""
경희대 캠퍼스맵에서 건물/층별 공간(강의실, 교수연구실 등)을 크롤링해 DB(classrooms 테이블)에 업서트합니다.
- 대상 URL: https://www.khu.ac.kr/kor/user/mapManager/view.do?menuNo=200357
- 층별 정보 API: /kor/user/mapManager/getFloorsInfoByMapId.json?mapId={mapId}
- 실행 결과는 JSON으로 stdout에 요약을 남깁니다.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 경로/환경 설정
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # .../agent-khu
BACKEND_DIR = REPO_ROOT / "backend"

load_dotenv()  # DB 접속 정보 반영

sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app import models  # noqa: E402
import parse_rooms as pr  # noqa: E402

BASE_URL = "https://www.khu.ac.kr"
CAMPUS_MENU_NO = "200357"  # 국제캠퍼스
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": f"{BASE_URL}/kor/user/mapManager/view.do?menuNo={CAMPUS_MENU_NO}",
}


@dataclass
class Building:
    map_id: int
    name: str
    lat: float
    lng: float
    map_number: int


@dataclass
class RoomRecord:
    building_name: str
    room_number: str
    room_label: str
    floor: str
    room_type: str
    professor_name: Optional[str]
    is_accessible: bool
    keywords: str
    latitude: float
    longitude: float


# ---------------------------------------------------------------------------
# 파싱/분류 유틸
# ---------------------------------------------------------------------------
ROOM_LINE_PATTERN = re.compile(r"([^\s]+)\s+(.*)")


def parse_buildings_from_html(html: str) -> List[Building]:
    """페이지에 인라인된 JSON을 추출해 건물 리스트를 만든다."""
    match = re.search(r"const jsonContent = JSON\.stringify\((\[[\s\S]*?\])\)", html)
    if not match:
        raise RuntimeError("jsonContent 블록을 찾지 못했습니다")

    buildings_raw = json.loads(match.group(1))
    buildings: List[Building] = []
    for b in buildings_raw:
        try:
            # ✅ 건물명 정규화: 줄바꿈, 탭, 여러 공백을 단일 공백으로 변환
            building_name = str(b["mapNm"]).strip()
            # 줄바꿈, 탭 제거 및 여러 공백을 단일 공백으로
            building_name = re.sub(r'[\r\n\t]+', ' ', building_name)
            building_name = re.sub(r'\s+', ' ', building_name).strip()
            
            buildings.append(
                Building(
                    map_id=int(b["mapId"]),
                    name=building_name,
                    lat=float(b["xCoord"]),
                    lng=float(b["yCoord"]),
                    map_number=int(b.get("mapNumber", 0) or 0),
                )
            )
        except Exception:
            continue
    return buildings


def fetch_buildings() -> List[Building]:
    resp = requests.get(
        f"{BASE_URL}/kor/user/mapManager/view.do?menuNo={CAMPUS_MENU_NO}",
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    return parse_buildings_from_html(resp.text)


def fetch_floor_data(map_id: int) -> List[Dict]:
    url = f"{BASE_URL}/kor/user/mapManager/getFloorsInfoByMapId.json?mapId={map_id}"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("floorData", [])


def parse_floor_desc(desc: str) -> List[tuple[str, str]]:
    """층 설명 문자열을 개별 호실/공간으로 분리한다."""
    rooms: List[tuple[str, str]] = []
    for raw_line in desc.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = ROOM_LINE_PATTERN.match(line)
        if not match:
            continue
        room_number, room_label = match.group(1).strip(), match.group(2).strip()
        if room_number == "0" or not room_label:
            continue
        rooms.append((room_number, room_label))
    return rooms


def infer_floor(room_number: str, fallback: Optional[str] = None) -> str:
    """호실 번호/코드에서 층 정보를 추정한다."""
    if not room_number:
        return fallback or ""

    if room_number[0] in {"B", "b"}:
        digits = re.match(r"[Bb](\d+)", room_number)
        if digits and digits.group(1):
            return f"B{digits.group(1)[0]}"
        return "B"

    digit_match = re.match(r"(\d)", room_number)
    if digit_match:
        return digit_match.group(1)

    if fallback:
        return fallback
    return ""


def normalize_floor_number(floor_number: Optional[str]) -> Optional[str]:
    if not floor_number:
        return None
    cleaned = floor_number.strip().upper().replace("F", "")
    return cleaned or None


def build_room_record(
    building: Building,
    room_number: str,
    room_label: str,
    floor_number: Optional[str],
) -> RoomRecord:
    floor = infer_floor(room_number, fallback=normalize_floor_number(floor_number))
    room_type = pr.classify_room_type(room_label)
    professor_name = pr.extract_professor_name(room_label) or None
    is_accessible = pr.is_accessible(room_type)
    keywords = pr.extract_keywords(room_label, room_type)

    return RoomRecord(
        building_name=building.name,
        room_number=room_number,
        room_label=room_label,
        floor=floor or (floor_number or ""),
        room_type=room_type,
        professor_name=professor_name,
        is_accessible=is_accessible,
        keywords=",".join(keywords),
        latitude=building.lat,
        longitude=building.lng,
    )


# ---------------------------------------------------------------------------
# DB 업서트
# ---------------------------------------------------------------------------

def upsert_classroom(db, record: RoomRecord) -> str:
    """classrooms 테이블에 업서트. 반환값: inserted/updated/skipped"""
    code = f"{record.building_name}_{record.room_number}"
    existing = db.query(models.Classroom).filter(models.Classroom.code == code).first()

    payload = {
        "code": code,
        "building_name": record.building_name,
        "room_number": record.room_number,
        "floor": str(record.floor),
        "room_name": record.room_label,
        "room_type": record.room_type,
        "professor_name": record.professor_name,
        "is_accessible": record.is_accessible,
        "keywords": record.keywords,
        "latitude": record.latitude,
        "longitude": record.longitude,
    }

    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
        db.commit()
        return "updated"

    db.add(models.Classroom(**payload))
    db.commit()
    return "inserted"


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------

def crawl() -> Dict:
    summary = {
        "buildings": 0,
        "rooms_processed": 0,
        "inserted": 0,
        "updated": 0,
        "errors": [],
    }

    db = SessionLocal()
    try:
        buildings = fetch_buildings()
        summary["buildings"] = len(buildings)

        for b in buildings:
            try:
                floors = fetch_floor_data(b.map_id)
            except Exception as e:  # noqa: BLE001
                summary["errors"].append(f"map_id={b.map_id}: {e}")
                continue

            for floor in floors:
                floor_desc = floor.get("floorDesc", "") or ""
                floor_number = floor.get("floorNumber")
                for room_number, room_label in parse_floor_desc(floor_desc):
                    record = build_room_record(b, room_number, room_label, floor_number)
                    summary["rooms_processed"] += 1
                    try:
                        result = upsert_classroom(db, record)
                        summary[result] += 1
                    except Exception as e:  # noqa: BLE001
                        db.rollback()
                        summary["errors"].append(
                            f"{record.building_name}/{room_number}: {e}"
                        )
    finally:
        db.close()

    return summary


if __name__ == "__main__":
    result = crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2))
