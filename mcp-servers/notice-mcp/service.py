"""
Notice service layer for DB-backed operations.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

backend_path = os.getenv("BACKEND_PATH", "/app")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal
from app import crud, models
import crawler


def get_department(db, department: str) -> Optional[models.Department]:
    return db.query(models.Department).filter(
        (models.Department.name == department) |
        (models.Department.code == department)
    ).first()


def list_latest_notices(department: str, limit: int = 5):
    db = SessionLocal()
    try:
        dept = get_department(db, department)
        if not dept:
            return None, {"error": {"type": "NotFound", "message": f"학과를 찾을 수 없습니다: {department}"}}

        notices = crud.get_latest_notices(db, source=dept.code, limit=limit)
        return dept, {"notices": [
            {
                "title": n.title,
                "url": n.url,
                "date": n.date,
                "author": n.author,
                "source": n.source,
                "views": n.views or 0,
            }
            for n in notices
        ]}
    finally:
        db.close()


def search_notices(query: str, limit: int = 5, department: Optional[str] = None):
    db = SessionLocal()
    try:
        dept = None
        if department:
            dept = get_department(db, department)

        notices = crud.search_notices(db, query, limit)
        if dept:
            notices = [n for n in notices if n.source == dept.code]
        return {
            "notices": [
                {
                    "title": n.title,
                    "url": n.url,
                    "date": n.date,
                    "author": n.author,
                    "source": n.source,
                    "views": n.views or 0,
                }
                for n in notices
            ]
        }
    finally:
        db.close()


def crawl_and_persist(department: str, limit: int = 20, keyword: Optional[str] = None):
    db = SessionLocal()
    try:
        dept = get_department(db, department)
        if not dept:
            return {"error": {"type": "NotFound", "message": f"학과를 찾을 수 없습니다: {department}"}}

        posts = crawler.crawl_department(dept, limit=limit, keyword=keyword, db=db)
        if not posts:
            msg = f"{dept.name} 신규 공지 없음" + (f" (키워드: {keyword})" if keyword else "")
            return {"success": True, "department": dept.name, "crawled": 0, "new_count": 0, "message": msg}

        new_count = sum(1 for post in posts if crud.create_notice_from_mcp(db, post))
        return {
            "success": True,
            "department": dept.name,
            "crawled": len(posts),
            "new_count": new_count,
            **({"keyword": keyword} if keyword else {}),
        }
    finally:
        db.close()
