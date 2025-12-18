"""
졸업요건 API 라우터
"""
import json
import subprocess
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(
    prefix="/api/curriculum",
    tags=["curriculum"]
)

# Curriculum MCP 스크래퍼 경로
# Docker 컨테이너 내에서는 /mcp-servers 볼륨이 마운트됨
MCP_SCRAPER_PATH = "/mcp-servers/curriculum-mcp/scrapers/requirements_scraper.py"


def sync_curriculum_data() -> dict:
    """
    MCP에서 졸업요건 데이터를 받아 DB에 동기화
    """
    try:
        print("🔄 MCP 졸업요건 데이터 동기화 시작...")
        
        # Python 스크래퍼 실행
        result = subprocess.run(
            ["python3", MCP_SCRAPER_PATH],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"❌ 스크래퍼 실패: {result.stderr}")
            return {"success": False, "message": result.stderr}
        
        print("✅ MCP 데이터 갱신 완료")
        return {"success": True, "message": "MCP 데이터 갱신 완료"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "스크래퍼 타임아웃"}
    except Exception as e:
        print(f"❌ 스크래퍼 오류: {e}")
        return {"success": False, "message": str(e)}


def load_curriculum_from_mcp(db: Session) -> dict:
    """
    MCP JSON 파일에서 데이터를 로드해서 DB에 저장
    """
    mcp_data_path = "/mcp-servers/curriculum-mcp/data/curriculum_data.json"
    
    try:
        if not os.path.exists(mcp_data_path):
            return {"success": False, "message": "MCP 데이터 파일 없음"}
        
        with open(mcp_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        loaded_count = 0
        
        # 각 연도별로 처리
        for year, year_data in data.items():
            if "programs" not in year_data:
                continue
            
            for program_code, program_data in year_data["programs"].items():
                # 프로그램명 추출
                program_name = program_data.get("program_name", "컴퓨터공학과")
                
                # 단일전공 기준 처리
                if "single_major" in program_data:
                    curriculum_dict = {
                        "year": year,
                        "program_code": program_code,
                        "program_name": program_name,
                        "track": "single_major",
                        **program_data
                    }
                    
                    result = crud.create_curriculum_from_mcp(
                        db,
                        curriculum_dict,
                        department=program_name
                    )
                    
                    if result:
                        loaded_count += 1
        
        print(f"✅ {loaded_count}개 졸업요건 DB 저장 완료")
        return {"success": True, "loaded_count": loaded_count, "message": f"{loaded_count}개 졸업요건 저장"}
    
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return {"success": False, "message": str(e)}


@router.get("/requirements")
async def get_requirements(
    admission_year: int,
    department: str = "컴퓨터공학부",
    db: Session = Depends(get_db)
):
    """
    졸업요건 조회
    
    Parameters:
    - admission_year: 입학년도 (2019, 2020, ...)
    - department: 학과명 (기본: 컴퓨터공학부)
    """
    curriculum = crud.get_curriculum(db, department, admission_year)
    
    if not curriculum:
        raise HTTPException(
            status_code=404,
            detail=f"{admission_year}학년도 {department} 졸업요건이 없습니다"
        )
    
    requirements = json.loads(curriculum.requirements)
    
    return {
        "admission_year": admission_year,
        "department": department,
        "requirements": requirements,
        "created_at": curriculum.created_at
    }


@router.post("/sync")
async def sync_requirements(db: Session = Depends(get_db)):
    """
    MCP 데이터를 동기화하고 DB에 저장
    - 스크래퍼 실행 → JSON 갱신
    - JSON에서 읽어 DB에 저장
    """
    # 1. 스크래퍼 실행
    sync_result = sync_curriculum_data()
    
    if not sync_result["success"]:
        raise HTTPException(status_code=500, detail=sync_result["message"])
    
    # 2. DB에 저장
    load_result = load_curriculum_from_mcp(db)
    
    return {
        "status": "success",
        "sync": sync_result,
        "load": load_result,
        "message": "졸업요건 데이터 동기화 완료"
    }


@router.get("/evaluation")
async def evaluate_graduation_progress(
    admission_year: int,
    completed_credits: int = 0,
    department: str = "컴퓨터공학부",
    db: Session = Depends(get_db)
):
    """
    졸업요건 진도율 평가
    
    Parameters:
    - admission_year: 입학년도
    - completed_credits: 이수한 전공학점
    - department: 학과명
    """
    curriculum = crud.get_curriculum(db, department, admission_year)
    
    if not curriculum:
        raise HTTPException(
            status_code=404,
            detail=f"{admission_year}학년도 {department} 졸업요건이 없습니다"
        )
    
    requirements = json.loads(curriculum.requirements)
    
    # 단일전공 기준으로 평가
    single_major = requirements.get("single_major", {})
    groups = single_major.get("groups", [])
    total_credits_required = single_major.get("total_credits", 130)
    major_credits_required = single_major.get("major_credits", 96)
    
    # 진도율 계산
    progress_percent = (completed_credits / total_credits_required * 100) if total_credits_required > 0 else 0
    remaining_credits = max(0, total_credits_required - completed_credits)
    
    return {
        "admission_year": admission_year,
        "department": department,
        "completed_credits": completed_credits,
        "total_credits_required": total_credits_required,
        "major_credits_required": major_credits_required,
        "remaining_credits": remaining_credits,
        "progress_percent": round(progress_percent, 1),
        "groups": groups,
        "special_requirements": requirements.get("special_requirements", {}),
        "status": "on_track" if progress_percent >= (completed_credits / 4 * 100) else "behind"  # 학년 기준
    }


@router.get("/list")
async def list_all_requirements(
    department: str = "컴퓨터공학부",
    db: Session = Depends(get_db)
):
    """
    학과의 모든 연도별 졸업요건 목록
    """
    curriculums = db.query(models.Curriculum).filter(
        models.Curriculum.department == department
    ).order_by(models.Curriculum.admission_year.desc()).all()
    
    if not curriculums:
        raise HTTPException(
            status_code=404,
            detail=f"{department} 졸업요건이 없습니다"
        )
    
    return {
        "department": department,
        "count": len(curriculums),
        "years": [
            {
                "admission_year": c.admission_year,
                "created_at": c.created_at,
                "total_credits": json.loads(c.requirements)
                    .get("single_major", {})
                    .get("total_credits", 0)
            }
            for c in curriculums
        ]
    }
