import os
import sys
from datetime import datetime

# Allow import of backend modules
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal  # noqa: E402
from app import models  # noqa: E402

DEPARTMENTS = [
    {"name": "소프트웨어융합학과", "code": "swedu", "notice_url": "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01", "notice_type": "standard"},
    {"name": "컴퓨터공학부", "code": "cse", "notice_url": "https://ce.khu.ac.kr/ce/notice/notice.do", "notice_type": "standard"},
    {"name": "전자공학과", "code": "ee", "notice_url": None, "notice_type": "standard"},
    {"name": "산업경영공학과", "code": "ime", "notice_url": None, "notice_type": "standard"},
]

NOTICES = [
    {
        "notice_id": "demo-1",
        "source": "swedu",
        "title": "[데모] 장학 안내",
        "content": "장학금 신청 공지 예시",
        "url": "https://swedu.khu.ac.kr/demo1",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "author": "학과사무실",
    },
    {
        "notice_id": "demo-2",
        "source": "cse",
        "title": "[데모] 수강신청 일정",
        "content": "수강신청 일정 안내",
        "url": "https://ce.khu.ac.kr/demo2",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "author": "학과사무실",
    },
]


def main():
    db = SessionLocal()
    try:
        # Departments
        for dept in DEPARTMENTS:
            existing = db.query(models.Department).filter(models.Department.code == dept["code"]).first()
            if not existing:
                db.add(models.Department(**dept))
        db.commit()

        # Notices
        for item in NOTICES:
            existing = db.query(models.Notice).filter(models.Notice.notice_id == item["notice_id"]).first()
            if existing:
                continue
            dept = db.query(models.Department).filter(models.Department.code == item["source"]).first()
            db.add(models.Notice(
                department=dept,
                is_active=True,
                views=0,
                crawled_at=datetime.now(),
                **item,
            ))
        db.commit()
        print("Seeded departments and notices (sqlite test DB)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
