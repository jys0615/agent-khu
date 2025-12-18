"""
Curriculum MCP Server - 교과과정 및 졸업요건 정보 제공
MCP SDK 호환
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
import json

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

DATA_PATH = (Path(__file__).resolve().parent / "data" / "curriculum_data.json")

# Server initialization
server = Server("curriculum-mcp")

_data_cache: dict | None = None


def _log(msg: str) -> None:
    try:
        print(msg, file=sys.stderr)
    except Exception:
        # In case stdio manages streams strictly, ignore logging failures
        pass


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
            
            _log(f"✅ 교과과정 데이터 로드: {total_courses}개 과목")
            return _data_cache
    else:
        _log("⚠️ 교과과정 데이터 없음")
        return {}


def get_all_courses(year: str = "latest") -> list[dict]:
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


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_curriculum",
            description="교과과정 과목 검색 (과목명, 과목코드, 분류로 검색)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어 (예: '자료구조', 'CS101')"
                    },
                    "year": {
                        "type": "string",
                        "description": "기준 연도 (기본값: latest)",
                        "default": "latest"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_curriculum_by_semester",
            description="학기별 과목 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "semester": {
                        "type": "string",
                        "description": "학기 (예: '1학기', '2학기')"
                    },
                    "year": {
                        "type": "string",
                        "description": "기준 연도",
                        "default": "latest"
                    }
                },
                "required": ["semester"]
            }
        ),
        Tool(
            name="list_programs",
            description="전공/프로그램 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "string",
                        "description": "기준 연도",
                        "default": "latest"
                    }
                }
            }
        ),
        Tool(
            name="get_requirements",
            description="졸업요건 조회 (사용자가 졸업요건, 졸업 조건 등을 물을 때 사용)",
            inputSchema={
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "프로그램 코드 (예: KHU-CSE). 비워두면 사용자 학과 적용",
                        "default": ""
                    },
                    "year": {
                        "type": "string",
                        "description": "입학년도. 비워두면 사용자 입학년도 적용",
                        "default": ""
                    }
                }
            }
        ),
        Tool(
            name="evaluate_progress",
            description="졸업요건 진행도 평가 (사용자가 진행도, 남은 학점 등을 물을 때 사용)",
            inputSchema={
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "프로그램 코드. 비워두면 사용자 학과 적용",
                        "default": ""
                    },
                    "year": {
                        "type": "string",
                        "description": "입학년도. 비워두면 사용자 입학년도 적용",
                        "default": ""
                    },
                    "taken_courses": {
                        "type": "array",
                        "description": "이수한 과목 목록 (과목코드 배열)",
                        "default": []
                    }
                }
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    global _data_cache
    if _data_cache is None:
        _data_cache = load_data()
    
    try:
        if name == "search_curriculum":
            query = arguments.get("query", "").strip().lower()
            year = arguments.get("year", "latest")
            
            if not query:
                result = json.dumps({
                    "found": False,
                    "error": "검색어를 입력해주세요",
                    "courses": []
                }, ensure_ascii=False)
            else:
                courses = get_all_courses(year)
                
                # 검색
                matches = []
                for course in courses:
                    name_str = course.get("name", "").lower()
                    code = course.get("code", "").lower()
                    group = course.get("group", "").lower()
                    
                    if query in name_str or query in code or query in group:
                        matches.append(course)
                
                if matches:
                    result = json.dumps({
                        "found": True,
                        "query": query,
                        "year": year,
                        "total": len(matches),
                        "courses": matches
                    }, ensure_ascii=False)
                else:
                    result = json.dumps({
                        "found": False,
                        "query": query,
                        "year": year,
                        "courses": [],
                        "error": f"'{query}'에 대한 검색 결과가 없습니다"
                    }, ensure_ascii=False)
        
        elif name == "get_curriculum_by_semester":
            semester = arguments.get("semester", "")
            year = arguments.get("year", "latest")
            
            # "1학기" → "1"
            sem_num = "1" if "1" in semester else "2" if "2" in semester else ""
            
            courses = get_all_courses(year)
            
            # 학기 필터링
            matches = []
            for course in courses:
                if sem_num in course.get("semesters", []):
                    matches.append(course)
            
            if matches:
                result = json.dumps({
                    "found": True,
                    "year": year,
                    "semester": semester,
                    "total": len(matches),
                    "courses": matches
                }, ensure_ascii=False)
            else:
                result = json.dumps({
                    "found": False,
                    "year": year,
                    "semester": semester,
                    "courses": [],
                    "error": f"{year}년 {semester}에 개설된 과목이 없습니다"
                }, ensure_ascii=False)
        
        elif name == "list_programs":
            year = arguments.get("year", "latest")
            if year == "latest":
                year = "2025"
            
            if year not in _data_cache or "programs" not in _data_cache[year]:
                result = json.dumps({
                    "found": False,
                    "programs": [],
                    "error": f"{year}년도 프로그램 정보를 찾을 수 없습니다"
                }, ensure_ascii=False)
            else:
                programs = []
                for prog_code, prog_data in _data_cache[year]["programs"].items():
                    name_str = prog_data.get("name", prog_data.get("program_name", prog_code))
                    credits = prog_data.get("total_credits", 0)
                    programs.append({
                        "code": prog_code,
                        "name": name_str,
                        "total_credits": credits
                    })
                
                result = json.dumps({
                    "found": True,
                    "programs": programs,
                    "year": year
                }, ensure_ascii=False)
        
        elif name == "get_requirements":
            program = arguments.get("program") or "KHU-CSE"
            year = arguments.get("year")
            
            # year가 명시적으로 전달되지 않았거나 "latest"인 경우만 기본값 사용
            if not year or year == "latest":
                year = "2025"
            
            # JSON 형식으로 응답
            if year not in _data_cache:
                result = json.dumps({
                    "found": False,
                    "error": f"{year}년도 데이터가 없습니다"
                }, ensure_ascii=False)
            elif "programs" not in _data_cache[year] or program not in _data_cache[year]["programs"]:
                result = json.dumps({
                    "found": False,
                    "error": f"{program} 프로그램 정보를 찾을 수 없습니다"
                }, ensure_ascii=False)
            else:
                prog_data = _data_cache[year]["programs"][program]
                prog_name = prog_data.get("program_name", prog_data.get("name", "컴퓨터공학과"))
                
                # single_major 정보
                if "single_major" in prog_data:
                    sm = prog_data["single_major"]
                    total_credits = sm.get("total_credits", 140)
                    major_credits = sm.get("major_credits", 60)
                    
                    groups = []
                    for group in sm.get("groups", []):
                        groups.append({
                            "name": group.get("name", ""),
                            "min_credits": group.get("min_credits", 0),
                            "description": group.get("description", "")
                        })
                    
                    result = json.dumps({
                        "found": True,
                        "program": program,
                        "program_name": prog_name,
                        "year": year,
                        "total_credits": total_credits,
                        "major_credits": major_credits,
                        "groups": groups,
                        "special_requirements": prog_data.get("special_requirements", {})
                    }, ensure_ascii=False)
                else:
                    result = json.dumps({
                        "found": False,
                        "error": f"{prog_name} 졸업요건 정보를 찾을 수 없습니다"
                    }, ensure_ascii=False)
        
        elif name == "evaluate_progress":
            program = arguments.get("program") or "KHU-CSE"
            year = arguments.get("year")
            taken_courses = arguments.get("taken_courses", [])
            
            # year가 명시적으로 전달되지 않았거나 "latest"인 경우만 기본값 사용
            if not year or year == "latest":
                year = "2025"
            
            # JSON 형식으로 응답
            if year not in _data_cache or "programs" not in _data_cache[year]:
                result = json.dumps({
                    "found": False,
                    "error": "데이터를 찾을 수 없습니다"
                }, ensure_ascii=False)
            else:
                prog_data = _data_cache[year]["programs"].get(program, {})
                prog_name = prog_data.get("program_name", "컴퓨터공학과")
                
                # 간단한 학점 계산 (취한 과목당 3학점)
                completed_credits = len(taken_courses) * 3
                total_credits = 140
                remaining = max(0, total_credits - completed_credits)
                progress = (completed_credits / total_credits) * 100 if total_credits > 0 else 0
                
                result = json.dumps({
                    "found": True,
                    "program": program,
                    "program_name": prog_name,
                    "year": year,
                    "completed_credits": completed_credits,
                    "total_credits": total_credits,
                    "remaining_credits": remaining,
                    "progress_percent": round(progress, 1),
                    "status": "completed" if progress >= 100 else "on_track" if progress >= 50 else "needs_attention"
                }, ensure_ascii=False)
        
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"오류: {str(e)}")]


async def main():
    """Main entry point"""
    global _data_cache
    _data_cache = load_data()
    
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
