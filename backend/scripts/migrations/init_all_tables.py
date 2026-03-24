"""
모든 테이블 생성
"""
from app.database import engine
from app import models

print("🔄 데이터베이스 테이블 생성 중...")

# 모든 테이블 생성
models.Base.metadata.create_all(bind=engine)

print("✅ 테이블 생성 완료:")
print("  - classrooms (강의실)")
print("  - notices (공지사항)")
print("  - meals (학식)")
print("  - library_seats (도서관)")
print("  - shuttle_buses (셔틀버스)")
print("  - courses (수강신청)")