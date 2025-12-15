#!/usr/bin/env python3
"""
Curriculum Scraper - 과목 카탈로그 + 졸업요건 통합
"""
from __future__ import annotations
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

import requests
from lxml import html as lxml_html

# 저장 경로
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum_data.json"
REQUIREMENTS_SCRAPER_PATH = Path(__file__).resolve().parent / "requirements_scraper.py"


def scrape_ce_curriculum(url: str = "https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600054") -> dict:
    """컴퓨터공학과 교과과정 크롤링 - 정확한 컬럼 인덱스 사용"""
    print(f"🔄 크롤링 시작: {url}")
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        doc = lxml_html.fromstring(resp.text)
        tables = doc.xpath("//table")
        
        catalog = []
        
        for table in tables:
            rows = table.xpath(".//tr")
            if len(rows) < 2:
                continue
            
            # 헤더 확인
            header = rows[0]
            headers = [td.text_content().strip() for td in header.xpath(".//th|.//td")]
            header_text = " ".join(headers)
            
            # 교과목 테이블인지 확인
            if not any(kw in header_text for kw in ["교과목", "학수번호", "학점"]):
                continue
            
            print(f"\n✅ 교과목 테이블 발견!")
            print(f"📋 헤더: {headers[:15]}")
            
            # 데이터 파싱
            last_group = ""  # rowspan 처리용
            
            for idx, row in enumerate(rows[1:]):
                cells = [td.text_content().strip() for td in row.xpath(".//td")]
                
                if len(cells) < 4:
                    continue
                
                try:
                    # rowspan 감지: 15개면 정상, 14개면 rowspan 중
                    has_group_col = (len(cells) >= 15)
                    
                    if has_group_col:
                        # 정상 행 (이수구분 포함)
                        group = cells[1]
                        name = cells[2]
                        code = cells[3]
                        credits_str = cells[4]
                        sem1_idx = 10
                        sem2_idx = 11
                        last_group = group  # 저장
                    else:
                        # rowspan 행 (이수구분 생략됨)
                        group = last_group  # 이전 값 사용
                        name = cells[1]     # 한 칸 앞으로
                        code = cells[2]
                        credits_str = cells[3]
                        sem1_idx = 9        # 한 칸 앞으로
                        sem2_idx = 10
                    
                    # 디버그 (처음 10개만)
                    if idx < 10:
                        print(f"\n🔍 Row {idx+1}: cells={len(cells)}개, rowspan={'없음' if has_group_col else '적용중'}")
                        print(f"   이수구분: {group}")
                        print(f"   교과목명: {name}")
                        print(f"   학수번호: {code}")
                        print(f"   학점: {credits_str}")
                        if len(cells) > sem1_idx:
                            print(f"   [{sem1_idx}] 1학기: '{cells[sem1_idx]}'")
                        if len(cells) > sem2_idx:
                            print(f"   [{sem2_idx}] 2학기: '{cells[sem2_idx]}'")
                    
                    # 학점 파싱
                    credits = 3
                    try:
                        match = re.search(r'\d+', credits_str)
                        if match:
                            credits = int(match.group())
                    except:
                        pass
                    
                    # 학기 정보
                    semesters = []
                    if len(cells) > sem1_idx and "○" in cells[sem1_idx]:
                        semesters.append("1")
                    if len(cells) > sem2_idx and "○" in cells[sem2_idx]:
                        semesters.append("2")
                    
                    # 유효성
                    if not code or not name:
                        continue
                    
                    item = {
                        "code": code,
                        "name": name,
                        "credits": credits,
                        "group": group,
                        "semesters": semesters
                    }
                    
                    catalog.append(item)
                    
                    if idx < 10:
                        print(f"   ✅ 파싱 완료: code={code}, name={name}, semesters={semesters}")
                
                except Exception as e:
                    if idx < 10:
                        print(f"   ❌ 에러: {e}")
                        import traceback
                        traceback.print_exc()
                    continue
        
        print(f"\n✅ 크롤링 완료: {len(catalog)}개 과목")
        
        # 자료구조 확인
        for item in catalog:
            if item["code"] == "CSE204":
                print(f"\n🎯 자료구조 발견: {json.dumps(item, ensure_ascii=False, indent=2)}")
                break
        
        return {
            "year": "2024",
            "catalog": catalog,
            "crawled_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


def save_data(data: dict) -> None:
    """데이터 저장"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 저장 완료: {DATA_PATH}")


def main():
    """메인 실행 - 과목 카탈로그 + 졸업요건 통합"""
    print("🔄 커리큘럼 전체 데이터 갱신 시작...\n")
    
    # 1. 기존 데이터 로드
    existing_data = {}
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        print("✅ 기존 데이터 로드 완료")
    
    # 2. 과목 카탈로그 크롤링 (2024년만 새로 크롤링)
    print("\n📚 과목 카탈로그 크롤링...")
    new_catalog = scrape_ce_curriculum()
    
    if not new_catalog or not new_catalog.get("catalog"):
        print("⚠️ 과목 크롤링 실패 - 기존 데이터 사용")
        new_catalog = existing_data.get("2024", {})
    else:
        print(f"✅ {len(new_catalog['catalog'])}개 과목 추출")
    
    # 3. 졸업요건 크롤링 (requirements_scraper 호출)
    print("\n📋 졸업요건 데이터 크롤링...")
    try:
        import sys
        sys.path.insert(0, str(REQUIREMENTS_SCRAPER_PATH.parent))
        from requirements_scraper import scrape_requirements, merge_requirements_with_catalog
        
        # 컴퓨터공학과 요건 크롤링
        req_data = scrape_requirements("ce")
        
        if req_data:
            print(f"✅ 졸업요건 데이터 추출 완료 ({len(req_data['requirements'])}개 연도)")
            # 기존 데이터와 통합
            final_data = merge_requirements_with_catalog(existing_data, req_data)
        else:
            print("⚠️ 졸업요건 크롤링 실패 - 기존 데이터 사용")
            final_data = existing_data
    
    except Exception as e:
        print(f"⚠️ 졸업요건 크롤링 오류: {e}")
        final_data = existing_data
    
    # 4. 저장
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ 전체 작업 완료")
    print(f"   - 과목: {len(new_catalog.get('catalog', []))}개")
    print(f"   - 저장 경로: {DATA_PATH}")
    print("="*60)


if __name__ == "__main__":
    main()