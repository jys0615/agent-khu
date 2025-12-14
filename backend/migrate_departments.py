"""
단과대/학과 데이터 마이그레이션 스크립트
기존 swedu/ime/ce를 Department로 변환하고 주요 학과 추가
"""
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal, engine
from app import models

# 테이블 생성
print("📦 테이블 생성 중...")
models.Base.metadata.create_all(bind=engine)
print("✅ 테이블 생성 완료")

db = SessionLocal()

try:
    # 1. 단과대 추가
    print("\n🏛️ 단과대 추가 중...")
    colleges_data = [
        {"name": "소프트웨어융합대학", "campus": "국제캠퍼스", "code": "swcon"},
        {"name": "공과대학", "campus": "국제캠퍼스", "code": "eng"},
        {"name": "전자정보대학", "campus": "국제캠퍼스", "code": "cse"},
        {"name": "경영대학", "campus": "서울캠퍼스", "code": "business"},
        {"name": "정경대학", "campus": "서울캠퍼스", "code": "polsci"},
        {"name": "이과대학", "campus": "서울캠퍼스", "code": "science"},
    ]
    
    for data in colleges_data:
        existing = db.query(models.College).filter_by(code=data['code']).first()
        if not existing:
            college = models.College(**data)
            db.add(college)
    
    db.commit()
    print(f"✅ {len(colleges_data)}개 단과대 추가")
    
    # 2. 학과/학부 추가
    print("\n📚 학과/학부 추가 중...")
    
    # 소프트웨어융합대학
    swcon_college = db.query(models.College).filter_by(code="swcon").first()
    # 공과대학
    eng_college = db.query(models.College).filter_by(code="eng").first()
    # 전자정보대학
    cse_college = db.query(models.College).filter_by(code="cse").first()
    
    departments_data = [
        # 소프트웨어융합대학
        {
            "college_id": swcon_college.id,
            "name": "소프트웨어융합학과",
            "code": "swedu",
            "notice_url": "http://swcon.khu.ac.kr/post/?mode=list&board_page=1",
            "notice_type": "custom"
        },
        {
            "college_id": swcon_college.id,
            "name": "컴퓨터공학부",
            "code": "ce",
            "notice_url": "https://ce.khu.ac.kr/ce/user/bbs/BMSR00040/list.do?menuNo=1600045",
            "notice_type": "standard"
        },
        
        # 공과대학
        {
            "college_id": eng_college.id,
            "name": "산업경영공학과",
            "code": "ime",
            "notice_url": "https://ie.khu.ac.kr/ie/user/bbs/BMSR00040/list.do?menuNo=17400015",
            "notice_type": "standard"
        },
        {
            "college_id": eng_college.id,
            "name": "기계공학과",
            "code": "me",
            "notice_url": None,  # 추후 추가
            "notice_type": "standard"
        },
        {
            "college_id": eng_college.id,
            "name": "화학공학과",
            "code": "chemeng",
            "notice_url": None,
            "notice_type": "standard"
        },
        {
            "college_id": eng_college.id,
            "name": "건축공학과",
            "code": "archieng",
            "notice_url": None,
            "notice_type": "standard"
        },
        
        # 전자정보대학
        {
            "college_id": cse_college.id,
            "name": "전자정보공학부",
            "code": "elec",
            "notice_url": None,
            "notice_type": "standard"
        },
    ]
    
    for data in departments_data:
        existing = db.query(models.Department).filter_by(code=data['code']).first()
        if not existing:
            dept = models.Department(**data)
            db.add(dept)
    
    db.commit()
    print(f"✅ {len(departments_data)}개 학과 추가")
    
    # 3. 기존 Notice 데이터에 department_id 매핑
    print("\n🔗 기존 공지사항 매핑 중...")
    
    # 이전 설정의 source → code 매핑
    source_to_code = {
        "swedu": "swedu",
        "ime": "ime",
        "ce": "ce"
    }
    
    # notices 테이블에 department_id 컬럼이 없으면 skip
    from sqlalchemy import inspect
    inspector = inspect(engine)
    notices_columns = [c['name'] for c in inspector.get_columns('notices')]
    
    if 'department_id' in notices_columns:
        for source, code in source_to_code.items():
            dept = db.query(models.Department).filter_by(code=code).first()
            if dept:
                updated = db.query(models.Notice).filter_by(source=source, department_id=None).update(
                    {"department_id": dept.id}
                )
                db.commit()
                print(f"  ✅ {source} → {dept.name}: {updated}개 공지 매핑")
    else:
        print("  ⚠️ department_id 컬럼이 없어 매핑 스킵 (init_db.py에서 처리)")
    
    # 최종 현황
    print("\n📊 최종 현황:")
    print(f"  단과대: {db.query(models.College).count()}개")
    print(f"  학과: {db.query(models.Department).count()}개")
    
    print("\n✨ 마이그레이션 완료!")
    print("\n  다음 단계:")
    print("  1. init_db.py 재실행 → DB 스키마 동기화")
    print("  2. backend restart → department_id 컬럼 추가 완료")

except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    db.rollback()
    raise
finally:
    db.close()
