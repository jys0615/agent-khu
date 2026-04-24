"""
Tool 실행 결과 누적 및 최종 API 응답 구성
"""
from typing import Optional, Any, Dict, List
from typing_extensions import TypedDict


class AccumulatedResults(TypedDict):
    classrooms: List[Dict]
    notices: List[Dict]
    map_links: List[str]
    courses: List[Dict]
    curriculum_courses: List[Dict]
    requirements_result: Optional[Dict]
    progress_result: Optional[Dict]
    library_info: Optional[Dict]
    library_seats: Optional[Dict]
    reservation: Optional[Dict]
    needs_library_login: bool
    meal_result: Optional[Any]


def empty_accumulated() -> AccumulatedResults:
    """빈 AccumulatedResults 초기화"""
    return {
        "classrooms": [],
        "notices": [],
        "map_links": [],
        "courses": [],
        "curriculum_courses": [],
        "requirements_result": None,
        "progress_result": None,
        "library_info": None,
        "library_seats": None,
        "reservation": None,
        "needs_library_login": False,
        "meal_result": None,
    }


def accumulate_results(accumulated: AccumulatedResults, tool_name: str, result: dict) -> None:
    """Tool 실행 결과를 누적 컨테이너에 추가 (in-place)"""
    if result.get("needs_login"):
        accumulated["needs_library_login"] = True

    if "classroom" in result:
        accumulated["classrooms"].append(result["classroom"])
        if "map_link" in result:
            accumulated["map_links"].append(result["map_link"])

    if "notices" in result:
        accumulated["notices"].extend(result["notices"])

    if tool_name in {"search_curriculum", "get_curriculum_by_semester"}:
        if isinstance(result.get("courses"), list):
            accumulated["curriculum_courses"].extend(result["courses"])
    elif isinstance(result.get("courses"), list):
        accumulated["courses"].extend(result["courses"])

    if tool_name == "get_requirements" and result.get("found"):
        accumulated["requirements_result"] = result["requirements"]

    if tool_name == "evaluate_progress" and result.get("found"):
        accumulated["progress_result"] = result["evaluation"]

    if tool_name == "get_library_info" and "library_info" in result:
        accumulated["library_info"] = result["library_info"]

    if tool_name == "get_seat_availability" and "library_seats" in result:
        accumulated["library_seats"] = result["library_seats"]

    if tool_name == "reserve_seat" and "reservation" in result:
        accumulated["reservation"] = result["reservation"]

    if tool_name == "get_today_meal" and "meals" in result:
        accumulated["meal_result"] = result["meals"]


def build_final_result(answer: str, accumulated: AccumulatedResults) -> Dict[str, Any]:
    """누적된 Tool 결과로 최종 API 응답 dict 구성"""
    result: Dict[str, Any] = {"message": answer}

    if accumulated["classrooms"]:
        result["classroom"] = accumulated["classrooms"][0]
        result["map_link"] = accumulated["map_links"][0] if accumulated["map_links"] else None
        result["show_map_button"] = True

    if accumulated["notices"]:
        result["notices"] = accumulated["notices"]
        result["show_notices"] = True

    if accumulated["courses"]:
        result["courses"] = accumulated["courses"]
        result["show_courses"] = True

    if accumulated["curriculum_courses"]:
        result["curriculum_courses"] = accumulated["curriculum_courses"]
        result["show_courses"] = True

    if accumulated["requirements_result"]:
        result["requirements"] = accumulated["requirements_result"]
        result["show_requirements"] = True
        _append_requirements_summary(result, accumulated["requirements_result"])

    if accumulated["progress_result"]:
        result["evaluation"] = accumulated["progress_result"]
        result["show_evaluation"] = True

    if accumulated["library_seats"]:
        result["library_seats"] = accumulated["library_seats"]
        result["show_library_seats"] = True
    elif accumulated["library_info"]:
        result["library_info"] = accumulated["library_info"]
        result["show_library_info"] = True

    if accumulated["reservation"]:
        result["reservation"] = accumulated["reservation"]
        result["show_reservation"] = True

    if accumulated["needs_library_login"]:
        result["needs_library_login"] = True

    if accumulated["meal_result"]:
        _append_meal_result(result, accumulated["meal_result"])

    return result


# ── private helpers ────────────────────────────────────────────────────────────

def _append_requirements_summary(result: Dict[str, Any], req: dict) -> None:
    """졸업요건 요약 텍스트를 메시지 뒤에 추가"""
    try:
        year = req.get("year")
        prog = req.get("program_name") or req.get("program")
        total = req.get("total_credits")
        major = req.get("major_credits")

        group_lines = [
            f"- {g.get('name')}: {g.get('min_credits')}학점"
            for g in (req.get("groups") or [])[:4]
            if g.get("name") and g.get("min_credits") is not None
        ]

        lines = [
            f"\n## 📋 {year}학번 {prog} 졸업요건 요약",
            f"- 총 이수학점: {total}학점",
            f"- 전공 이수학점: {major}학점",
        ]
        if group_lines:
            lines.append("- 전공 이수 구분:")
            lines.extend(group_lines)

        result["message"] = (result["message"] or "").rstrip() + "\n" + "\n".join(lines)
    except Exception:
        pass


def _append_meal_result(result: Dict[str, Any], meal: Any) -> None:
    """학식 결과를 응답에 추가하고 원본 링크를 메시지에 삽입"""
    result["meals"] = meal
    result["show_meals"] = True
    try:
        # meal은 list([meal_info]) — 첫 번째 항목에서 URL 추출
        first = meal[0] if isinstance(meal, list) and meal else None
        item = first if first is not None else (meal if isinstance(meal, dict) else None)
        if item:
            src = item.get("source_url") or item.get("menu_url")
            if src and src not in result["message"]:
                result["message"] = result["message"].rstrip() + f"\n원본 메뉴표: {src}"
    except Exception:
        pass
