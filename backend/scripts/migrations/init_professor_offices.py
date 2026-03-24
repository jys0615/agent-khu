# backend/init_professor_offices.py
import asyncio
from app.database import SessionLocal
from app import models
from mcp_servers.classroom_mcp.scrapers.professor_scraper import scrape_professor_offices

async def main():
    db = SessionLocal()
    
    # 크롤링
    professors = await scrape_professor_offices()
    
    # DB 삽입
    for prof in professors:
        classroom = models.Classroom(
            code=prof["room_code"],          # "7056"
            building_name=prof["building"],   # "우정원"
            room_number=prof["room_code"],    # "7056"
            floor=prof["floor"],              # "7F"
            room_name=f"{prof['professor_name']} 교수 연구실",
            room_type="교수연구실",
            professor_name=prof["professor_name"],  # "김민호"
            is_accessible=True,
            keywords=f"{prof['professor_name']},교수,연구실,{prof['building']}",
            latitude=prof["latitude"],
            longitude=prof["longitude"]
        )
        db.add(classroom)
    
    db.commit()
    print(f"✅ {len(professors)}개 교수 연구실 등록 완료")

if __name__ == "__main__":
    asyncio.run(main())
