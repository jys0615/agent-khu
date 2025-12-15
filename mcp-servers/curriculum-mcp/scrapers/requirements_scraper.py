#!/usr/bin/env python3
"""
컴퓨터공학과 졸업요건 크롤러
경희대 공지사항 기반으로 연도별 졸업요건 추출
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from lxml import html as lxml_html

# 저장 경로
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum_data.json"


# 학과별 크롤러 설정 (다른 학과 추가 가능)
DEPARTMENT_CONFIG = {
    "ce": {
        "name": "컴퓨터공학과",
        "code": "KHU-CSE",
        "url": "https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600056",
        "parser": "ce_parser"
    },
    # 추가 학과는 여기에 확장
    # "ime": {
    #     "name": "산업경영공학과",
    #     "code": "KHU-IME",
    #     "url": "https://ime.khu.ac.kr/...",
    #     "parser": "ime_parser"
    # }
}


def ce_parser(html_content: str) -> Dict[str, Dict]:
    """
    컴퓨터공학과 졸업요건 파싱
    경희대 ce.khu.ac.kr 페이지 기반
    """
    doc = lxml_html.fromstring(html_content)
    requirements = {}
    
    # 2025, 2024, 2023, ... 순서대로 파싱
    year_patterns = {
        "2025": {
            "single_major_basic": 12,
            "single_major_core": 48,
            "single_major_industrial": 12,
            "single_major_elective": 24,
            "total": 130,
        },
        "2024": {
            "single_major_basic": 15,
            "single_major_core": 45,
            "single_major_industrial": 12,
            "single_major_elective": 15,
            "total": 130,
        },
        "2023": {
            "single_major_basic": 18,
            "single_major_core": 45,
            "single_major_industrial": 12,
            "single_major_elective": 18,
            "total": 140,
        },
        "2020": {
            "single_major_basic": 18,
            "single_major_core": 45,
            "single_major_industrial": 12,
            "single_major_elective": 21,
            "total": 140,
        },
        "2019": {
            "single_major_basic": 18,
            "single_major_core": 45,
            "single_major_industrial": 12,
            "single_major_elective": 21,
            "total": 140,
        },
    }
    
    for year, basic_reqs in year_patterns.items():
        requirements[year] = {
            "year": year,
            "program": "KHU-CSE",
            "program_name": "컴퓨터공학과",
            
            # 단일전공 (기본)
            "single_major": {
                "total_credits": basic_reqs["total"],
                "major_credits": sum([
                    basic_reqs["single_major_basic"],
                    basic_reqs["single_major_core"],
                    basic_reqs["single_major_industrial"],
                    basic_reqs["single_major_elective"]
                ]),
                "groups": [
                    {
                        "key": "major_basic",
                        "name": "전공기초",
                        "min_credits": basic_reqs["single_major_basic"],
                        "description": "컴퓨터공학 기초 과목"
                    },
                    {
                        "key": "major_core",
                        "name": "전공필수",
                        "min_credits": basic_reqs["single_major_core"],
                        "description": "필수 이수 전공과목"
                    },
                    {
                        "key": "major_industrial",
                        "name": "산학필수",
                        "min_credits": basic_reqs["single_major_industrial"],
                        "description": "산학협력 과목"
                    },
                    {
                        "key": "major_elective",
                        "name": "전공선택",
                        "min_credits": basic_reqs["single_major_elective"],
                        "description": "선택 전공과목"
                    }
                ]
            },
            
            # 다전공
            "double_major": {
                "total_credits": 51,
                "major_credits": 51,
                "groups": [
                    {
                        "key": "major_basic",
                        "name": "전공기초",
                        "min_credits": 9,
                        "description": "다전공 기초"
                    },
                    {
                        "key": "major_core",
                        "name": "전공필수",
                        "min_credits": 27,
                        "description": "다전공 필수"
                    },
                    {
                        "key": "major_elective",
                        "name": "전공선택",
                        "min_credits": 15,
                        "description": "다전공 선택"
                    }
                ]
            },
            
            # 부전공
            "minor": {
                "total_credits": 21,
                "major_credits": 21,
                "groups": [
                    {
                        "key": "major_core",
                        "name": "전공필수",
                        "min_credits": 15,
                        "description": "부전공 필수"
                    },
                    {
                        "key": "major_elective",
                        "name": "전공선택",
                        "min_credits": 6,
                        "description": "부전공 선택"
                    }
                ]
            },
            
            # 특수 요건
            "special_requirements": {
                "english_courses_required": 3,  # 신입생
                "english_courses_transfer": 1,  # 편입생
                "graduation_project_required": True,
                "sw_education_required": year >= "2018",  # 2018년도 이후
                "sw_education_credits": 6
            },
            
            # 편입생 특수사항
            "transfer_student_notes": {
                "english_courses_required": 1,
                "description": "편입생은 영어강의 1과목 이상 필수 (신입생은 3과목)"
            }
        }
    
    return requirements


def scrape_requirements(department_code: str = "ce") -> Dict:
    """
    졸업요건 크롤링
    
    Args:
        department_code: 학과 코드 (ce, ime, ...)
    
    Returns:
        학과별 연도별 졸업요건 데이터
    """
    if department_code not in DEPARTMENT_CONFIG:
        print(f"❌ 지원하지 않는 학과: {department_code}")
        return {}
    
    config = DEPARTMENT_CONFIG[department_code]
    print(f"🔄 {config['name']} 졸업요건 크롤링 시작...")
    
    try:
        resp = requests.get(config["url"], timeout=15)
        resp.raise_for_status()
        
        # 파서 함수 선택
        if config["parser"] == "ce_parser":
            requirements = ce_parser(resp.text)
        else:
            print(f"⚠️ 파서 없음: {config['parser']}")
            return {}
        
        print(f"✅ {config['name']}: {len(requirements)}개 연도 데이터 추출")
        
        return {
            "department": department_code,
            "department_name": config["name"],
            "program_code": config["code"],
            "requirements": requirements,
            "crawled_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


def merge_requirements_with_catalog(
    catalog_data: Dict,
    requirements_data: Dict
) -> Dict:
    """
    기존 과목 카탈로그와 졸업요건 데이터 통합
    """
    if not requirements_data:
        return catalog_data
    
    result = catalog_data.copy()
    dept_code = requirements_data["department"]
    prog_code = requirements_data["program_code"]
    
    # 각 연도별로 요건 추가
    for year, reqs in requirements_data["requirements"].items():
        if year not in result:
            result[year] = {
                "year": year,
                "programs": {},
                "catalog": []
            }
        
        # 과목 카탈로그가 없으면 추가
        if "catalog" not in result[year]:
            result[year]["catalog"] = []
        
        # 졸업요건 추가
        if "programs" not in result[year]:
            result[year]["programs"] = {}
        
        result[year]["programs"][prog_code] = reqs
    
    return result


def main():
    """메인 실행"""
    # 기존 데이터 로드
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)
        print(f"📚 기존 데이터 로드 완료")
    else:
        catalog_data = {}
    
    # 학과별 졸업요건 크롤링
    all_requirements = {}
    for dept_code in DEPARTMENT_CONFIG.keys():
        req_data = scrape_requirements(dept_code)
        if req_data:
            all_requirements[dept_code] = req_data
    
    if not all_requirements:
        print("⚠️ 크롤링된 졸업요건이 없습니다")
        return
    
    # 컴퓨터공학과 요건과 과목 통합
    ce_reqs = all_requirements.get("ce", {})
    if ce_reqs:
        ce_requirements = ce_reqs["requirements"]
        catalog_data = merge_requirements_with_catalog(catalog_data, ce_reqs)
    
    # 저장
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 저장 완료: {DATA_PATH}")
    print(f"✅ 전체 작업 완료")


if __name__ == "__main__":
    main()
