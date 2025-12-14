"""
Curriculum MCP Server - 연도별 데이터 구조 지원
"""
from __future__ import annotations
import json
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_PATH = (Path(__file__).resolve().parent / "data" / "curriculum_data.json")

_data_cache: Optional[dict] = None


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
    """데이터 파일 로드"""
    global _data_cache
    
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _data_cache = json.load(f)
            
            # 과목 수 계산
            total_courses = 0
            for year in ["2019", "2024", "2025"]:
                if year in _data_cache and "catalog" in _data_cache[year]:
                    total_courses += len(_data_cache[year]["catalog"])
            
            print(f"✅ 교과과정 데이터 로드: {total_courses}개 과목")
            return _data_cache
    else:
        print("⚠️ 교과과정 데이터 없음")
        return {}


def get_all_courses(year: str = "latest") -> List[Dict]:
    """모든 연도의 과목 가져오기"""
    global _data_cache
    
    if _data_cache is None:
        _data_cache = load_data()
    
    # latest = 가장 최신 연도 (2025)
    if year == "latest":
        year = "2025"
    
    # 해당 연도 데이터
    if year in _data_cache and "catalog" in _data_cache[year]:
        return _data_cache[year]["catalog"]
    
    return []


async def tool_search_curriculum(args: Dict) -> Dict:
    """교과과정 과목 검색"""
    query = args.get("query", "").strip().lower()
    year = args.get("year", "latest")
    
    if not query:
        return {"found": False, "courses": []}
    
    courses = get_all_courses(year)
    
    # 검색
    results = []
    for course in courses:
        name = course.get("name", "").lower()
        code = course.get("code", "").lower()
        group = course.get("group", "").lower()
        
        if query in name or query in code or query in group:
            results.append({
                "code": course.get("code", ""),
                "name": course.get("name", ""),
                "credits": course.get("credits", 0),
                "group": course.get("group", ""),
                "semesters": course.get("semesters", [])
            })
    
    return {
        "found": len(results) > 0,
        "courses": results[:20]
    }


async def tool_get_curriculum_by_semester(args: Dict) -> Dict:
    """학기별 과목 조회"""
    semester = args.get("semester", "")
    year = args.get("year", "latest")
    
    # "1학기" → "1"
    sem_num = "1" if "1" in semester else "2" if "2" in semester else ""
    
    courses = get_all_courses(year)
    
    # 학기 필터링
    results = []
    for course in courses:
        if sem_num in course.get("semesters", []):
            results.append({
                "code": course.get("code", ""),
                "name": course.get("name", ""),
                "credits": course.get("credits", 0),
                "group": course.get("group", ""),
                "semesters": course.get("semesters", [])
            })
    
    return {
        "found": len(results) > 0,
        "courses": results
    }


async def tool_list_programs(args: Dict) -> Dict:
    """전공 목록 조회"""
    global _data_cache
    
    if _data_cache is None:
        _data_cache = load_data()
    
    year = args.get("year", "latest")
    if year == "latest":
        year = "2025"
    
    programs = []
    if year in _data_cache and "programs" in _data_cache[year]:
        for prog_code, prog_data in _data_cache[year]["programs"].items():
            programs.append({
                "code": prog_code,
                "name": prog_data.get("name", ""),
                "total_credits": prog_data.get("total_credits", 0)
            })
    
    return {
        "found": True,
        "programs": programs
    }


async def tool_get_requirements(args: Dict) -> Dict:
    """졸업요건 조회"""
    global _data_cache
    
    if _data_cache is None:
        _data_cache = load_data()
    
    program = args.get("program", "KHU-CSE")
    year = args.get("year", "latest")
    
    if year == "latest":
        year = "2025"
    
    if year in _data_cache and "programs" in _data_cache[year]:
        prog_data = _data_cache[year]["programs"].get(program, {})
        
        if prog_data:
            return {
                "found": True,
                "program": program,
                "name": prog_data.get("name", ""),
                "total_credits": prog_data.get("total_credits", 130),
                "groups": prog_data.get("groups", [])
            }
    
    return {"found": False}


async def tool_evaluate_progress(args: Dict) -> Dict:
    """졸업요건 평가"""
    program = args.get("program", "KHU-CSE")
    year = args.get("year", "latest")
    taken = args.get("taken_courses", [])
    
    return {
        "found": True,
        "completed_credits": len(taken) * 3,
        "remaining_credits": 130 - (len(taken) * 3),
        "progress_percent": (len(taken) * 3 / 130) * 100
    }


async def main():
    global _data_cache
    
    # 데이터 미리 로드
    _data_cache = load_data()
    
    tools = {
        "search_curriculum": tool_search_curriculum,
        "get_curriculum_by_semester": tool_get_curriculum_by_semester,
        "list_programs": tool_list_programs,
        "get_requirements": tool_get_requirements,
        "evaluate_progress": tool_evaluate_progress
    }
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "curriculum-mcp",
                        "version": "1.0.0"
                    }
                }
            })
            continue
        
        if msg.get("method") == "notifications/initialized":
            continue
        
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "search_curriculum",
                            "description": "교과과정 과목 검색",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "year": {"type": "string"}
                                }
                            }
                        },
                        {
                            "name": "get_curriculum_by_semester",
                            "description": "학기별 과목 조회",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "semester": {"type": "string"},
                                    "year": {"type": "string"}
                                }
                            }
                        },
                        {
                            "name": "list_programs",
                            "description": "전공 목록",
                            "inputSchema": {"type": "object", "properties": {"year": {"type": "string"}}}
                        },
                        {
                            "name": "get_requirements",
                            "description": "졸업요건",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "program": {"type": "string"},
                                    "year": {"type": "string"}
                                }
                            }
                        },
                        {
                            "name": "evaluate_progress",
                            "description": "졸업요건 평가",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "program": {"type": "string"},
                                    "year": {"type": "string"},
                                    "taken_courses": {"type": "array"}
                                }
                            }
                        }
                    ]
                }
            })
            continue
        
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
                print(f"❌ Tool 에러: {e}", file=sys.stderr)
                _result(req_id, {"error": str(e)}, is_error=True)
            continue
        
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})


if __name__ == "__main__":
    asyncio.run(main())
