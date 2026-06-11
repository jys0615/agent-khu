"""
Curriculum MCP Server — FastMCP + Streamable HTTP (Phase 2)
교과과정, 졸업요건 정보 제공
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List

from fastmcp import FastMCP

DATA_PATH = Path(__file__).resolve().parent / "data" / "curriculum_data.json"
PORT = int(os.getenv("PORT", "8106"))

mcp = FastMCP("curriculum-mcp")
_data_cache: dict | None = None


def _load_data() -> dict:
    global _data_cache
    if _data_cache is not None:
        return _data_cache
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            _data_cache = json.load(f)
        total = sum(
            len(_data_cache[y].get("catalog", []))
            for y in ["2019", "2024", "2025"]
            if y in _data_cache
        )
        print(f"✅ 교과과정 데이터 로드: {total}개 과목", file=sys.stderr)
    else:
        _data_cache = {}
        print("⚠️ 교과과정 데이터 없음", file=sys.stderr)
    return _data_cache


_YEAR_FALLBACK = {
    "2021": "2020",
    "2022": "2023",
}


def _resolve_year(year: str) -> str:
    """데이터가 없는 연도를 가장 가까운 연도로 매핑"""
    if year == "latest":
        return "2025"
    data = _load_data()
    if year in data:
        return year
    fallback = _YEAR_FALLBACK.get(year)
    if fallback and fallback in data:
        print(f"⚠️ {year}년도 데이터 없음 → {fallback}년도로 대체", file=sys.stderr)
        return fallback
    # 가장 가까운 연도 선택
    available = sorted(data.keys())
    if not available:
        return year
    try:
        yr = int(year)
        closest = min(available, key=lambda y: abs(int(y) - yr))
        print(f"⚠️ {year}년도 데이터 없음 → {closest}년도로 대체", file=sys.stderr)
        return closest
    except ValueError:
        return available[-1]


def _get_courses(year: str = "latest") -> list[dict]:
    data = _load_data()
    year = _resolve_year(year)
    return data.get(year, {}).get("catalog", [])


@mcp.tool()
async def search_curriculum(query: str, year: str = "latest") -> dict:
    """교과과정 과목 검색 (과목명, 과목코드, 분류로 검색)

    Args:
        query: 검색어 (예: '자료구조', 'CS101')
        year: 기준 연도 (기본값: latest = 2025)
    """
    q = query.strip().lower()
    if not q:
        return {"found": False, "error": "검색어를 입력해주세요", "courses": []}

    matches = [
        c for c in _get_courses(year)
        if q in c.get("name", "").lower()
        or q in c.get("code", "").lower()
        or q in c.get("group", "").lower()
    ]
    if matches:
        return {"found": True, "query": query, "year": year, "total": len(matches), "courses": matches}
    return {"found": False, "query": query, "year": year, "courses": [], "error": f"'{query}'에 대한 검색 결과가 없습니다"}


@mcp.tool()
async def get_curriculum_by_semester(semester: str, year: str = "latest") -> dict:
    """학기별 과목 조회

    Args:
        semester: 학기 (예: '1학기', '2학기')
        year: 기준 연도 (기본값: latest)
    """
    sem_num = "1" if "1" in semester else "2" if "2" in semester else ""
    matches = [c for c in _get_courses(year) if sem_num in c.get("semesters", [])]
    if matches:
        return {"found": True, "year": year, "semester": semester, "total": len(matches), "courses": matches}
    return {"found": False, "year": year, "semester": semester, "courses": [], "error": f"{year}년 {semester}에 개설된 과목이 없습니다"}


@mcp.tool()
async def list_programs(year: str = "latest") -> dict:
    """전공/프로그램 목록 조회

    Args:
        year: 기준 연도 (기본값: latest)
    """
    data = _load_data()
    year = _resolve_year(year)
    progs = data.get(year, {}).get("programs", {})
    if not progs:
        return {"found": False, "programs": [], "error": f"{year}년도 프로그램 정보를 찾을 수 없습니다"}
    programs = [
        {
            "code": code,
            "name": p.get("name", p.get("program_name", code)),
            "total_credits": p.get("total_credits", 0),
        }
        for code, p in progs.items()
    ]
    return {"found": True, "programs": programs, "year": year}


@mcp.tool()
async def get_requirements(program: str = "KHU-CSE", year: str = "2025") -> dict:
    """졸업요건 조회

    Args:
        program: 프로그램 코드 (예: KHU-CSE)
        year: 입학년도 (기본값: 2025)
    """
    data = _load_data()
    year = _resolve_year(year or "latest")
    if year not in data:
        return {"found": False, "error": f"{year}년도 데이터가 없습니다"}
    progs = data[year].get("programs", {})
    if program not in progs:
        return {"found": False, "error": f"{program} 프로그램 정보를 찾을 수 없습니다"}

    p = progs[program]
    prog_name = p.get("program_name", p.get("name", "컴퓨터공학과"))
    sm = p.get("single_major", {})
    groups = [
        {"name": g.get("name", ""), "min_credits": g.get("min_credits", 0), "description": g.get("description", "")}
        for g in sm.get("groups", [])
    ]
    return {
        "found": True,
        "program": program,
        "program_name": prog_name,
        "year": year,
        "total_credits": sm.get("total_credits", 140),
        "major_credits": sm.get("major_credits", 60),
        "groups": groups,
        "special_requirements": p.get("special_requirements", {}),
    }


@mcp.tool()
async def evaluate_progress(
    program: str = "KHU-CSE",
    year: str = "2025",
    taken_courses: List[str] = [],
) -> dict:
    """졸업요건 진행도 평가

    Args:
        program: 프로그램 코드
        year: 입학년도
        taken_courses: 이수한 과목 코드 목록
    """
    data = _load_data()
    year = _resolve_year(year or "latest")
    progs = data.get(year, {}).get("programs", {})
    p = progs.get(program, {})
    prog_name = p.get("program_name", "컴퓨터공학과")
    completed = len(taken_courses) * 3
    total = 140
    remaining = max(0, total - completed)
    pct = round((completed / total) * 100, 1) if total else 0
    return {
        "found": True,
        "program": program,
        "program_name": prog_name,
        "year": year,
        "completed_credits": completed,
        "total_credits": total,
        "remaining_credits": remaining,
        "progress_percent": pct,
        "status": "completed" if pct >= 100 else "on_track" if pct >= 50 else "needs_attention",
    }


if __name__ == "__main__":
    _load_data()
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
