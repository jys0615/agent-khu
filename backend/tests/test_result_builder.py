"""
result_builder 모듈 단위 테스트

외부 서비스(DB, Redis, Elasticsearch, MCP) 의존성 없음.
CI 환경에서 직접 실행 가능.
"""
import pytest
from app.agent.result_builder import (
    empty_accumulated,
    accumulate_results,
    build_final_result,
)


# ── empty_accumulated ──────────────────────────────────────────────────────────

def test_empty_accumulated_list_fields_are_empty():
    acc = empty_accumulated()
    assert acc["classrooms"] == []
    assert acc["notices"] == []
    assert acc["map_links"] == []
    assert acc["courses"] == []
    assert acc["curriculum_courses"] == []


def test_empty_accumulated_optional_fields_are_none():
    acc = empty_accumulated()
    assert acc["requirements_result"] is None
    assert acc["progress_result"] is None
    assert acc["library_info"] is None
    assert acc["library_seats"] is None
    assert acc["reservation"] is None
    assert acc["meal_result"] is None


def test_empty_accumulated_login_flag_is_false():
    acc = empty_accumulated()
    assert acc["needs_library_login"] is False


# ── accumulate_results ─────────────────────────────────────────────────────────

def test_accumulate_classroom():
    acc = empty_accumulated()
    accumulate_results(acc, "search_classroom", {
        "classroom": {"code": "T101", "building_name": "전자정보대학"},
        "map_link": "https://maps.google.com/?q=37,127",
    })
    assert len(acc["classrooms"]) == 1
    assert acc["classrooms"][0]["code"] == "T101"
    assert len(acc["map_links"]) == 1


def test_accumulate_classroom_without_map_link():
    acc = empty_accumulated()
    accumulate_results(acc, "search_classroom", {
        "classroom": {"code": "T101"},
    })
    assert len(acc["classrooms"]) == 1
    assert len(acc["map_links"]) == 0


def test_accumulate_notices_extends_list():
    acc = empty_accumulated()
    accumulate_results(acc, "search_notices", {"notices": [{"title": "공지1"}]})
    accumulate_results(acc, "get_latest_notices", {"notices": [{"title": "공지2"}, {"title": "공지3"}]})
    assert len(acc["notices"]) == 3


def test_accumulate_curriculum_courses_go_to_separate_bucket():
    acc = empty_accumulated()
    accumulate_results(acc, "search_curriculum", {"found": True, "courses": [{"name": "자료구조"}]})
    accumulate_results(acc, "get_curriculum_by_semester", {"found": True, "courses": [{"name": "알고리즘"}]})
    accumulate_results(acc, "search_courses", {"found": True, "courses": [{"name": "선형대수"}]})

    assert len(acc["curriculum_courses"]) == 2
    assert len(acc["courses"]) == 1


def test_accumulate_requirements_only_when_found():
    acc = empty_accumulated()
    req = {"year": "2021", "program_name": "컴퓨터공학과", "total_credits": 130, "major_credits": 60}

    accumulate_results(acc, "get_requirements", {"found": True, "requirements": req})
    assert acc["requirements_result"] == req

    acc2 = empty_accumulated()
    accumulate_results(acc2, "get_requirements", {"found": False})
    assert acc2["requirements_result"] is None


def test_accumulate_progress_only_when_found():
    acc = empty_accumulated()
    ev = {"completed": 90, "remaining": 40}

    accumulate_results(acc, "evaluate_progress", {"found": True, "evaluation": ev})
    assert acc["progress_result"] == ev

    acc2 = empty_accumulated()
    accumulate_results(acc2, "evaluate_progress", {"found": False})
    assert acc2["progress_result"] is None


def test_accumulate_library_login_flag():
    acc = empty_accumulated()
    accumulate_results(acc, "get_seat_availability", {"needs_login": True})
    assert acc["needs_library_login"] is True


def test_accumulate_library_seats():
    acc = empty_accumulated()
    seats = {"available": 10, "total": 50}
    accumulate_results(acc, "get_seat_availability", {"library_seats": seats})
    assert acc["library_seats"] == seats


def test_accumulate_meal():
    acc = empty_accumulated()
    meal = [{"cafeteria": "학생회관", "menu": "비빔밥", "price": 5000}]
    accumulate_results(acc, "get_today_meal", {"meals": meal})
    assert acc["meal_result"] == meal


# ── build_final_result ─────────────────────────────────────────────────────────

def test_build_basic_message():
    result = build_final_result("안녕하세요", empty_accumulated())
    assert result["message"] == "안녕하세요"


def test_build_no_extra_keys_when_empty():
    result = build_final_result("응답", empty_accumulated())
    for key in ("classroom", "notices", "courses", "requirements", "library_seats"):
        assert key not in result


def test_build_with_classroom():
    acc = empty_accumulated()
    acc["classrooms"] = [{"code": "T101", "building_name": "전자정보대학"}]
    acc["map_links"] = ["https://maps.google.com/..."]
    result = build_final_result("강의실 찾았습니다.", acc)
    assert result["classroom"]["code"] == "T101"
    assert result["show_map_button"] is True


def test_build_with_notices():
    acc = empty_accumulated()
    acc["notices"] = [{"title": "공지1"}, {"title": "공지2"}]
    result = build_final_result("공지사항입니다.", acc)
    assert len(result["notices"]) == 2
    assert result["show_notices"] is True


def test_build_library_seats_takes_priority_over_info():
    """library_seats와 library_info가 둘 다 있으면 seats가 우선돼야 한다."""
    acc = empty_accumulated()
    acc["library_seats"] = {"available": 10}
    acc["library_info"] = {"name": "중앙도서관"}
    result = build_final_result("도서관 정보", acc)
    assert "library_seats" in result
    assert result["show_library_seats"] is True
    assert "library_info" not in result


def test_build_requirements_appends_summary_to_message():
    acc = empty_accumulated()
    acc["requirements_result"] = {
        "year": "2021",
        "program_name": "컴퓨터공학과",
        "total_credits": 130,
        "major_credits": 60,
        "groups": [{"name": "전공필수", "min_credits": 24}],
    }
    result = build_final_result("졸업요건입니다.", acc)
    assert "졸업요건 요약" in result["message"]
    assert "130학점" in result["message"]
    assert "전공필수" in result["message"]
    assert result["show_requirements"] is True


def test_build_meal_appends_source_url():
    acc = empty_accumulated()
    acc["meal_result"] = {"source_url": "https://khu.ac.kr/meal", "menu": "비빔밥"}
    result = build_final_result("오늘의 학식입니다.", acc)
    assert "https://khu.ac.kr/meal" in result["message"]
    assert result["show_meals"] is True


def test_build_needs_library_login_flag():
    acc = empty_accumulated()
    acc["needs_library_login"] = True
    result = build_final_result("로그인이 필요합니다.", acc)
    assert result["needs_library_login"] is True
