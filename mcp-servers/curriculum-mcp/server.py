"""
Curriculum MCP Server v2 - 자동 갱신 지원
교과과정 데이터 제공 + 실시간 크롤링 + 변경 감지
"""
from __future__ import annotations
import json
import re
import sys
import asyncio
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import requests
from lxml import html as lxml_html

DATA_PATH = (Path(__file__).resolve().parent / "data" / "curriculum_data.json")
CACHE_PATH = (Path(__file__).resolve().parent / "data" / "cache.json")
UPDATE_INTERVAL = 86400  # 24시간 (초 단위)

# 전역 캐시
_data_cache: Optional[dict] = None
_last_update: Optional[datetime] = None
_update_task: Optional[asyncio.Task] = None


def _readline() -> Optional[dict]:
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except Exception:
        return None


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _result(id_: int, data: Any, is_error: bool = False):
    content = [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
    res = {
        "jsonrpc": "2.0",
        "id": id_,
        "result": {"content": content, "isError": is_error}
    }
    _send(res)


def load_data() -> dict:
    """교과과정 데이터 로드 (캐시 우선)"""
    global _data_cache, _last_update
    
    # 캐시가 있으면 반환
    if _data_cache:
        return _data_cache
    
    # JSON 파일에서 로드
    if not DATA_PATH.exists():
        return {}
    
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        _data_cache = json.load(f)
        _last_update = datetime.now()
    
    return _data_cache


def save_data(data: dict) -> None:
    """데이터 저장"""
    global _data_cache, _last_update
    
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    _data_cache = data
    _last_update = datetime.now()
    print(f"✅ 데이터 저장 완료: {_last_update}")


def calculate_hash(data: dict) -> str:
    """데이터 해시 계산 (변경 감지용)"""
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def load_cache_info() -> dict:
    """캐시 메타데이터 로드"""
    if not CACHE_PATH.exists():
        return {"last_hash": "", "last_crawl": None}
    
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache_info(hash_value: str) -> None:
    """캐시 메타데이터 저장"""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache_info = {
        "last_hash": hash_value,
        "last_crawl": datetime.now().isoformat()
    }
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_info, f, ensure_ascii=False, indent=2)


# ==========================================
# 실시간 크롤링 함수
# ==========================================

def crawl_ce_curriculum(url: str = "https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600054") -> dict:
    """컴퓨터공학과 교과과정 크롤링 (rowspan 처리)"""
    try:
        print(f"🔄 크롤링 시작: {url}")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        doc = lxml_html.fromstring(resp.text)
        
        # 테이블 찾기
        tables = doc.xpath("//table")
        catalog = []
        
        for table in tables:
            rows = table.xpath(".//tr")
            if len(rows) < 2:
                continue
            
            # 헤더 확인
            header = rows[0]
            headers = [td.text_content().strip() for td in header.xpath(".//th|.//td")]
            
            # 교과목 테이블인지 확인
            if not any(kw in " ".join(headers) for kw in ["교과목", "학수번호", "학점"]):
                continue
            
            print(f"✅ 교과목 테이블 발견!")
            
            # 데이터 파싱 (rowspan 처리)
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
                
                except Exception as e:
                    continue
        
        print(f"✅ 크롤링 완료: {len(catalog)}개 과목")
        
        return {
            "year": "2025",  # 현재 년도
            "catalog": catalog,
            "crawled_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def update_curriculum_data() -> bool:
    """교과과정 데이터 업데이트 (변경사항 있을 때만)"""
    try:
        # 기존 데이터 로드
        old_data = load_data()
        cache_info = load_cache_info()
        old_hash = cache_info.get("last_hash", "")
        
        # 새 데이터 크롤링
        new_catalog = crawl_ce_curriculum()
        
        if not new_catalog or not new_catalog.get("catalog"):
            print("⚠️ 크롤링 데이터 없음, 기존 데이터 유지")
            return False
        
        # 새 데이터 구성
        new_data = old_data.copy() if old_data else {}
        year = new_catalog["year"]
        
        # 졸업요건 (기본값, 추후 개선 가능)
        programs = {
            "KHU-CSE": {
                "name": "컴퓨터공학전공",
                "total_credits": 130,
                "groups": [
                    {"key": "major_basic", "name": "전공기초", "min_credits": 12},
                    {"key": "major_core", "name": "전공필수", "min_credits": 48},
                    {"key": "major_elective", "name": "전공선택", "min_credits": 24},
                    {"key": "liberal_core", "name": "핵심교양", "min_credits": 15}
                ],
                "policies": {
                    "english_major_courses_required": 3
                }
            }
        }
        
        new_data[year] = {
            "year": year,
            "programs": programs,
            "catalog": new_catalog["catalog"],
            "crawled_at": new_catalog["crawled_at"]
        }
        
        # 해시 비교
        new_hash = calculate_hash(new_data)
        
        if new_hash != old_hash:
            print(f"🔄 변경 감지! 데이터 업데이트")
            save_data(new_data)
            save_cache_info(new_hash)
            return True
        else:
            print(f"✅ 변경 없음, 기존 데이터 유지")
            return False
            
    except Exception as e:
        print(f"❌ 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def background_updater():
    """백그라운드 업데이트 태스크"""
    while True:
        try:
            print(f"🕐 업데이트 체크 시작: {datetime.now()}")
            await update_curriculum_data()
            print(f"⏰ 다음 업데이트: {UPDATE_INTERVAL}초 후")
            await asyncio.sleep(UPDATE_INTERVAL)
        except Exception as e:
            print(f"❌ 백그라운드 업데이트 에러: {e}")
            await asyncio.sleep(3600)  # 에러 시 1시간 대기


# ==========================================
# 기존 Tool 함수들
# ==========================================

def pick_year_blob(data: dict, year: Optional[str]) -> dict:
    """연도 선택 (latest면 가장 최신)"""
    if not data:
        return {}
    if not year or year == "latest":
        years = [y for y in data.keys() if y.isdigit()]
        if years:
            year = max(years)
        else:
            year = next(iter(data.keys())) if data else None
    return data.get(year, {}) if year else {}


async def tool_list_programs(args: dict) -> dict:
    """전공 프로그램 목록 조회"""
    data = load_data()
    blob = pick_year_blob(data, args.get("year"))
    progs = blob.get("programs", {}) if isinstance(blob, dict) else {}
    return {
        "year": blob.get("year", args.get("year", "latest")),
        "programs": list(progs.keys())
    }


async def tool_get_requirements(args: dict) -> Any:
    """전공별 졸업요건 조회"""
    program = args.get("program")
    data = load_data()
    blob = pick_year_blob(data, args.get("year"))
    programs = blob.get("programs", {})
    
    if program not in programs:
        return {
            "error": f"unknown program: {program}",
            "available": list(programs.keys())
        }
    
    return {
        "program": program,
        "year": blob.get("year"),
        **programs[program]
    }


async def tool_search_courses(args: dict) -> Any:
    """교과과정 과목 검색"""
    data = load_data()
    blob = pick_year_blob(data, args.get("year"))
    catalog = blob.get("catalog", []) or []
    query = (args.get("query", "") or "").lower().strip()
    
    if not query:
        return {"year": blob.get("year"), "courses": [], "count": 0, "found": False}
    
    results = []
    for item in catalog:
        code = str(item.get("code", "")).lower()
        name = str(item.get("name", "")).lower()
        group = str(item.get("group", "")).lower()
        
        if query in code or query in name or query in group:
            results.append(item)
    
    return {
        "year": blob.get("year"),
        "courses": results,
        "count": len(results),
        "found": bool(results)
    }


async def tool_force_update(args: dict) -> dict:
    """강제 업데이트 (수동 호출용)"""
    success = await update_curriculum_data()
    return {
        "success": success,
        "message": "업데이트 완료" if success else "변경사항 없음 또는 실패",
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# MCP 메인 루프
# ==========================================

async def main():
    global _update_task
    
    tools = {
        "list_programs": tool_list_programs,
        "get_requirements": tool_get_requirements,
        "search_courses": tool_search_courses,
        "force_update": tool_force_update,  # 🆕 강제 업데이트
    }
    
    # 초기 데이터 로드 (빠르게)
    load_data()
    
    # 🔧 백그라운드 태스크는 초기화 후 시작
    background_started = False
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        # initialize
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}}
                }
            })
            continue
        
        # notifications/initialized
        if msg.get("method") == "notifications/initialized":
            # 🆕 초기화 완료 후 백그라운드 태스크 시작
            if not background_started:
                _update_task = asyncio.create_task(background_updater())
                print("🚀 백그라운드 업데이트 태스크 시작")
                background_started = True
            continue
        
        # tools/list
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "list_programs",
                            "description": "전공 프로그램 목록 조회",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "year": {"type": "string", "default": "latest"}
                                }
                            }
                        },
                        {
                            "name": "get_requirements",
                            "description": "전공별 졸업요건 조회",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "program": {"type": "string"},
                                    "year": {"type": "string", "default": "latest"}
                                },
                                "required": ["program"]
                            }
                        },
                        {
                            "name": "search_courses",
                            "description": "교과과정 과목 검색",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "year": {"type": "string", "default": "latest"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "force_update",
                            "description": "🆕 교과과정 데이터 강제 업데이트",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            })
            continue
        
        # tools/call
        if msg.get("method") == "tools/call":
            req_id = msg.get("id")
            params = msg.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if name not in tools:
                _result(req_id, {"error": f"Unknown tool: {name}"}, is_error=True)
                continue
            
            try:
                result = await tools[name](arguments)
                _result(req_id, result)
            except Exception as e:
                import traceback
                traceback.print_exc()
                _result(req_id, {"error": str(e)}, is_error=True)
            continue
        
        # 기타
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 서버 종료")