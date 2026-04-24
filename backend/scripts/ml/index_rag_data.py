"""
RAG 지식 인덱싱 스크립트

PostgreSQL DB에서 데이터를 읽어 Elasticsearch RAG 인덱스에 적재.
스케줄러 또는 수동으로 실행.

사용법:
    # 전체 재인덱싱
    python scripts/index_rag_data.py

    # 특정 카테고리만
    python scripts/index_rag_data.py --category meal
    python scripts/index_rag_data.py --category notice
    python scripts/index_rag_data.py --category classroom
    python scripts/index_rag_data.py --category shuttle
"""
import sys
import os
import asyncio
import argparse
from datetime import datetime, timedelta

# backend/ 루트를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag_agent import get_rag_agent
from app.database import SessionLocal
from app import models


# ───────────────────────────── 카테고리별 인덱서 ─────────────────────────────

async def index_meals(rag, db) -> int:
    """오늘 + 내일 학식 메뉴 인덱싱"""
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    expires = (datetime.now() + timedelta(hours=12)).isoformat()

    meals = (
        db.query(models.Meal)
        .filter(models.Meal.date.in_([today, tomorrow]))
        .all()
    )

    docs = []
    for meal in meals:
        doc_id = f"meal-{meal.cafeteria}-{meal.date}-{meal.meal_type}"
        meal_type_kr = {"breakfast": "아침", "lunch": "점심", "dinner": "저녁"}.get(
            meal.meal_type, meal.meal_type
        )
        title = f"{meal.date} {meal.cafeteria} {meal_type_kr} 메뉴"
        price_str = f" ({meal.price}원)" if meal.price else ""
        content = f"{meal.date} {meal.cafeteria} {meal_type_kr} 식단{price_str}:\n{meal.menu}"

        docs.append(
            {
                "doc_id": doc_id,
                "category": "meal",
                "title": title,
                "content": content,
                "metadata": {
                    "cafeteria": meal.cafeteria,
                    "meal_type": meal.meal_type,
                    "date": meal.date,
                    "price": meal.price,
                },
                "expires_at": expires,
            }
        )

    deleted = await rag.delete_by_category("meal")
    indexed = await rag.bulk_index(docs)
    print(f"  [meal] 삭제 {deleted}건 → 인덱싱 {indexed}/{len(docs)}건")
    return indexed


async def index_notices(rag, db) -> int:
    """최근 30건 공지사항 인덱싱"""
    notices = (
        db.query(models.Notice)
        .filter(models.Notice.is_active == True)
        .order_by(models.Notice.crawled_at.desc())
        .limit(30)
        .all()
    )

    docs = []
    for notice in notices:
        doc_id = f"notice-{notice.notice_id}"
        content_parts = [f"제목: {notice.title}"]
        if notice.content:
            content_parts.append(notice.content[:500])
        if notice.url:
            content_parts.append(f"원문: {notice.url}")

        docs.append(
            {
                "doc_id": doc_id,
                "category": "notice",
                "title": notice.title,
                "content": "\n".join(content_parts),
                "metadata": {
                    "source": notice.source,
                    "date": notice.date,
                    "url": notice.url,
                    "author": notice.author,
                },
            }
        )

    deleted = await rag.delete_by_category("notice")
    indexed = await rag.bulk_index(docs)
    print(f"  [notice] 삭제 {deleted}건 → 인덱싱 {indexed}/{len(docs)}건")
    return indexed


async def index_classrooms(rag, db) -> int:
    """강의실/연구실 정보 인덱싱"""
    classrooms = db.query(models.Classroom).all()

    docs = []
    for room in classrooms:
        doc_id = f"classroom-{room.code}"
        title = f"{room.building_name} {room.room_number} ({room.room_name})"
        content_parts = [
            f"건물: {room.building_name}",
            f"호실: {room.room_number}",
            f"층: {room.floor}층",
            f"용도: {room.room_name} ({room.room_type})",
        ]
        if room.professor_name:
            content_parts.append(f"담당 교수: {room.professor_name}")
        if room.keywords:
            content_parts.append(f"키워드: {room.keywords}")

        docs.append(
            {
                "doc_id": doc_id,
                "category": "classroom",
                "title": title,
                "content": "\n".join(content_parts),
                "metadata": {
                    "code": room.code,
                    "building_name": room.building_name,
                    "room_number": room.room_number,
                    "latitude": room.latitude,
                    "longitude": room.longitude,
                },
            }
        )

    deleted = await rag.delete_by_category("classroom")
    indexed = await rag.bulk_index(docs)
    print(f"  [classroom] 삭제 {deleted}건 → 인덱싱 {indexed}/{len(docs)}건")
    return indexed


async def index_shuttle(rag) -> int:
    """셔틀 시간표 인덱싱 (정적 데이터)"""
    # 셔틀 시간표 정적 데이터 (MCP 서버 데이터와 동기화)
    shuttle_data = [
        {
            "doc_id": "shuttle-international-to-seoul",
            "title": "국제캠퍼스 → 서울캠퍼스 셔틀버스 시간표",
            "content": (
                "국제캠퍼스에서 서울캠퍼스 방향 셔틀버스 시간표:\n"
                "평일: 07:30, 08:00, 08:30, 09:00, 10:00, 11:00, 12:00, "
                "13:00, 14:00, 15:00, 16:00, 17:00, 18:00, 19:00\n"
                "토요일: 08:00, 10:00, 12:00, 14:00, 16:00\n"
                "일요일/공휴일: 운행 없음\n"
                "소요시간: 약 40~60분 (교통 상황에 따라 변동)"
            ),
            "metadata": {"direction": "international_to_seoul", "type": "shuttle"},
        },
        {
            "doc_id": "shuttle-seoul-to-international",
            "title": "서울캠퍼스 → 국제캠퍼스 셔틀버스 시간표",
            "content": (
                "서울캠퍼스에서 국제캠퍼스 방향 셔틀버스 시간표:\n"
                "평일: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, "
                "16:00, 17:00, 18:00, 19:00, 20:00\n"
                "토요일: 09:00, 11:00, 13:00, 15:00, 17:00\n"
                "일요일/공휴일: 운행 없음\n"
                "소요시간: 약 40~60분 (교통 상황에 따라 변동)"
            ),
            "metadata": {"direction": "seoul_to_international", "type": "shuttle"},
        },
        {
            "doc_id": "shuttle-general-info",
            "title": "경희대학교 셔틀버스 일반 안내",
            "content": (
                "경희대학교 셔틀버스(KHU 셔틀)는 국제캠퍼스(용인 수지)와 "
                "서울캠퍼스(회기역) 간을 운행합니다.\n"
                "탑승 위치: 국제캠퍼스 - 정문 앞 셔틀버스 정류장\n"
                "탑승 위치: 서울캠퍼스 - 학생회관 앞\n"
                "학기 중에만 운행하며, 방학 중 시간표는 별도 공지됩니다.\n"
                "셔틀버스 앱: KHU 앱에서 실시간 위치 확인 가능"
            ),
            "metadata": {"type": "shuttle_info"},
        },
    ]

    docs = [
        {
            "doc_id": d["doc_id"],
            "category": "shuttle",
            "title": d["title"],
            "content": d["content"],
            "metadata": d["metadata"],
        }
        for d in shuttle_data
    ]

    deleted = await rag.delete_by_category("shuttle")
    indexed = await rag.bulk_index(docs)
    print(f"  [shuttle] 삭제 {deleted}건 → 인덱싱 {indexed}/{len(docs)}건")
    return indexed


async def index_library(rag) -> int:
    """도서관 기본 정보 인덱싱 (정적)"""
    library_docs = [
        {
            "doc_id": "library-hours-global",
            "category": "library",
            "title": "경희대학교 국제캠퍼스 중앙도서관 운영시간",
            "content": (
                "경희대학교 국제캠퍼스 중앙도서관 운영시간:\n"
                "학기 중 평일: 08:00 ~ 22:00\n"
                "학기 중 토요일: 09:00 ~ 18:00\n"
                "일요일/공휴일: 휴관\n"
                "방학 중 평일: 09:00 ~ 18:00\n"
                "방학 중 토요일: 09:00 ~ 13:00\n"
                "열람실은 층별로 운영시간이 다를 수 있습니다."
            ),
            "metadata": {"campus": "global", "type": "library_hours"},
        },
        {
            "doc_id": "library-info-global",
            "category": "library",
            "title": "경희대학교 국제캠퍼스 중앙도서관 안내",
            "content": (
                "경희대학교 국제캠퍼스 중앙도서관:\n"
                "위치: 국제캠퍼스 중앙 도서관 건물\n"
                "열람실: 1열람실(1층), 2열람실(2층), 3열람실(3층), 멀티미디어실\n"
                "좌석 예약: 도서관 홈페이지 또는 KHU 앱에서 가능\n"
                "대출 권수: 학부생 5권 (14일)\n"
                "문의: 031-201-2200"
            ),
            "metadata": {"campus": "global", "type": "library_info"},
        },
    ]

    deleted = await rag.delete_by_category("library")
    indexed = await rag.bulk_index(library_docs)
    print(f"  [library] 삭제 {deleted}건 → 인덱싱 {indexed}/{len(library_docs)}건")
    return indexed


# ───────────────────────────── 메인 ─────────────────────────────

INDEXERS = {
    "meal":      lambda rag, db: index_meals(rag, db),
    "notice":    lambda rag, db: index_notices(rag, db),
    "classroom": lambda rag, db: index_classrooms(rag, db),
    "shuttle":   lambda rag, db: index_shuttle(rag),
    "library":   lambda rag, db: index_library(rag),
}


async def run(category: str = "all"):
    rag = get_rag_agent()
    await rag.initialize()

    # 인덱스가 없어도 bulk_index가 생성하므로 계속 진행
    db = SessionLocal()
    total = 0

    try:
        targets = list(INDEXERS.keys()) if category == "all" else [category]
        print(f"\n{'='*50}")
        print(f"RAG 인덱싱 시작: {', '.join(targets)}")
        print(f"{'='*50}")

        for cat in targets:
            if cat not in INDEXERS:
                print(f"  [오류] 알 수 없는 카테고리: {cat}")
                continue
            try:
                count = await INDEXERS[cat](rag, db)
                total += count
            except Exception as e:
                print(f"  [{cat}] 인덱싱 실패: {e}")

        stats = await rag.get_stats()
        print(f"\n{'='*50}")
        print(f"완료: 총 {total}건 인덱싱")
        print(f"인덱스 현황: {stats.get('by_category', {})}")
        print(f"{'='*50}\n")

    finally:
        db.close()
        await rag.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG 지식 인덱싱")
    parser.add_argument(
        "--category",
        default="all",
        choices=["all"] + list(INDEXERS.keys()),
        help="인덱싱할 카테고리 (기본: all)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.category))
