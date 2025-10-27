"""
셔틀버스 시간표 초기 데이터 입력
PDF/이미지에서 수작업으로 입력
"""
import json
from app.database import SessionLocal
from app import models

db = SessionLocal()

# 셔틀버스 데이터 (실제 시간표에 맞게 수정 필요)
shuttle_data = [
    {
        "route": "국제-서울캠",
        "departure": "국제캠퍼스",
        "arrival": "서울캠퍼스",
        "weekday_times": json.dumps([
            "08:00", "09:00", "10:00", "11:00", 
            "12:00", "13:00", "14:00", "15:00",
            "16:00", "17:00", "18:00", "19:00"
        ]),
        "weekend_times": json.dumps([
            "09:00", "11:00", "13:00", "15:00", "17:00"
        ]),
        "semester_type": "학기중",
        "note": "배차 간격 약 1시간"
    },
    {
        "route": "서울-국제캠",
        "departure": "서울캠퍼스",
        "arrival": "국제캠퍼스",
        "weekday_times": json.dumps([
            "08:30", "09:30", "10:30", "11:30",
            "12:30", "13:30", "14:30", "15:30",
            "16:30", "17:30", "18:30", "19:30"
        ]),
        "weekend_times": json.dumps([
            "09:30", "11:30", "13:30", "15:30", "17:30"
        ]),
        "semester_type": "학기중"
    },
    {
        "route": "기숙사 셔틀",
        "departure": "기숙사",
        "arrival": "전자정보대",
        "weekday_times": json.dumps([
            "08:20", "09:20", "10:20", "11:20",
            "12:20", "13:20", "14:20", "15:20",
            "16:20", "17:20", "18:20"
        ]),
        "weekend_times": json.dumps([
            "10:00", "14:00", "18:00"
        ]),
        "semester_type": "학기중",
        "note": "수업 시작 10분 전 도착 예정"
    }
]

# DB 저장
for shuttle in shuttle_data:
    existing = db.query(models.ShuttleBus).filter(
        models.ShuttleBus.route == shuttle["route"],
        models.ShuttleBus.semester_type == shuttle["semester_type"]
    ).first()
    
    if not existing:
        shuttle_obj = models.ShuttleBus(**shuttle)
        db.add(shuttle_obj)

db.commit()
print(f"✅ {len(shuttle_data)}개 셔틀버스 시간표 저장 완료")