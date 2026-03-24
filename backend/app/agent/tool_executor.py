"""
Tool 실행 핸들러 (캐싱 적용)
"""
import json
import hashlib
import logging
from typing import Optional, Any, Dict
from ..mcp_client import mcp_client
from .. import models
from ..database import SessionLocal
from ..cache import cache_manager
from .tools_definition import CACHE_TTL

log = logging.getLogger(__name__)


async def process_tool_call(
    tool_name: str,
    tool_input: dict,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    library_password: Optional[str] = None,
    current_user: Optional[models.User] = None
) -> Dict[str, Any]:
    """Tool 호출 처리 (캐싱 적용)"""
    try:
        # 🔥 캐시 불가능한 Tool (실시간 데이터)
        NO_CACHE_TOOLS = {
            "get_seat_availability",  # 도서관 좌석 (실시간)
            "reserve_seat",           # 예약 (상태 변경)
            "crawl_fresh_notices",    # 크롤링 (항상 최신)
        }
        
        # 캐시 키 생성 (사용자 컨텍스트를 반영해서 키 충돌 방지)
        cache_key = None
        if tool_name not in NO_CACHE_TOOLS:
            # 기본 입력
            derived_input = dict(tool_input or {})

            # 사용자 정보 기반으로 program/year 확정 (get_requirements / evaluate_progress)
            if tool_name in {"get_requirements", "evaluate_progress"}:
                # 학과 → 프로그램 매핑
                dept_map = {
                    "컴퓨터공학과": "KHU-CSE",
                    "컴퓨터공학부": "KHU-CSE",
                    "소프트웨어융합학과": "KHU-SW",
                    "인공지능학과": "KHU-AI",
                }

                program = derived_input.get("program")
                year = derived_input.get("year")

                if current_user:
                    if not program:
                        program = dept_map.get(current_user.department, "KHU-CSE")
                    if not year:
                        year = str(current_user.admission_year)

                # latest는 실제 값으로 정규화 (캐시 키 안정화)
                if (not year) or (year == "latest"):
                    year = "2025"

                derived_input["_program_resolved"] = program or "KHU-CSE"
                derived_input["_year_resolved"] = year

                # 진행도 평가는 수강 과목 구성도 캐시 키에 반영
                if tool_name == "evaluate_progress":
                    courses = derived_input.get("taken_courses") or []
                    # 정렬 + 해시로 간략화
                    try:
                        courses_norm = sorted(map(str, courses))
                    except Exception:
                        courses_norm = []
                    courses_hash = hashlib.md5(
                        json.dumps(courses_norm, ensure_ascii=False).encode("utf-8")
                    ).hexdigest()[:16]
                    derived_input["_courses_hash"] = courses_hash

            # tool_input(또는 파생 입력)을 정렬하여 일관된 키 생성
            sorted_input = json.dumps(derived_input, sort_keys=True, ensure_ascii=False)
            key_base = f"tool:{tool_name}:{sorted_input}"
            
            # 긴 키는 해시 처리
            if len(key_base) > 200:
                hash_suffix = hashlib.md5(key_base.encode()).hexdigest()[:16]
                cache_key = f"tool:{tool_name}:{hash_suffix}"
            else:
                cache_key = key_base
            
            # 캐시 조회
            cached = await cache_manager.get(cache_key)
            if cached:
                log.debug("Cache HIT: %s", tool_name)
                return cached
            else:
                log.debug("Cache MISS: %s", tool_name)
        
        # Tool 실행
        if tool_name == "search_classroom":
            result = await _handle_search_classroom(tool_input, user_latitude, user_longitude)
        
        elif tool_name == "search_notices":
            result = await _handle_search_notices(tool_input)
        
        elif tool_name == "get_latest_notices":
            result = await _handle_get_latest_notices(tool_input, current_user)
        
        elif tool_name == "crawl_fresh_notices":
            result = await _handle_crawl_fresh_notices(tool_input)
        
        elif tool_name == "search_meals":
            result = await _handle_search_meals(tool_input)
        
        elif tool_name == "get_next_shuttle":
            result = await _handle_get_next_shuttle(tool_input)
        
        elif tool_name == "search_courses":
            result = await _handle_search_courses(tool_input)
        
        elif tool_name == "search_curriculum":
            result = await _handle_search_curriculum(tool_input)
        
        elif tool_name == "get_curriculum_by_semester":
            result = await _handle_get_curriculum_by_semester(tool_input)
        
        elif tool_name == "list_programs":
            result = await _handle_list_programs(tool_input)
        
        elif tool_name == "get_requirements":
            result = await _handle_get_requirements(tool_input, current_user)
        
        elif tool_name == "evaluate_progress":
            result = await _handle_evaluate_progress(tool_input, current_user)
        
        elif tool_name == "get_library_info":
            result = await _handle_get_library_info(tool_input)
        
        elif tool_name == "get_seat_availability":
            result = await _handle_get_seat_availability(tool_input, library_username, library_password, current_user)
        
        elif tool_name == "reserve_seat":
            result = await _handle_reserve_seat(tool_input, library_username, library_password, current_user)
        
        elif tool_name == "get_today_meal":
            result = await _handle_get_today_meal(tool_input)
        
        elif tool_name == "get_cafeteria_info":
            result = await _handle_get_cafeteria_info()
        
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        # 캐시 저장
        if cache_key and not result.get("error") and not result.get("needs_login"):
            ttl = CACHE_TTL.get(tool_name, 3600)
            await cache_manager.set(cache_key, result, ttl)
            log.debug("Cache SAVE: %s (TTL: %ss)", tool_name, ttl)

        return result

    except Exception as e:
        log.error("Tool 실행 에러: %s", e)
        return {"error": str(e)}


async def _handle_search_classroom(tool_input: dict, user_latitude: Optional[float], user_longitude: Optional[float]):
    query = tool_input.get("query", "")
    
    result = await mcp_client.call_tool("classroom", "search_classroom", {"query": query}, timeout=10.0, retries=2)
    
    data = json.loads(result) if isinstance(result, str) else result
    
    if not data or not data.get("found"):
        return {"message": f"'{query}'에 대한 검색 결과가 없습니다."}
    
    # ✅ 'classrooms' (수정됨)
    room = data["classrooms"][0]
    # 지도 링크: 좌표만 있어도 목적지 링크 제공, 사용자 위치가 있으면 경로 안내
    map_link = None
    if room.get("latitude") and room.get("longitude"):
        origin_param = ""
        if user_latitude and user_longitude:
            origin_param = f"&origin={user_latitude},{user_longitude}"
        map_link = (
            f"https://www.google.com/maps/dir/?api=1"
            f"{origin_param}"
            f"&destination={room['latitude']},{room['longitude']}"
        )
    
    return {
        "classroom": {
            "code": room.get("code", ""),
            "building_name": room.get("building_name", ""),  # ✅ 수정: building → building_name
            "room_number": room.get("room_number", ""),
            "floor": room.get("floor", ""),
            "room_name": room.get("room_name", ""),  # ✅ 수정: name → room_name
            "room_type": room.get("room_type", "classroom"),
            "professor_name": room.get("professor_name"),
            "is_accessible": room.get("is_accessible", True),
            "latitude": room.get("latitude"),
            "longitude": room.get("longitude")
        },
        "map_link": map_link,
        "show_map_button": map_link is not None
    }



async def _handle_search_notices(tool_input: dict):
    query = tool_input.get("query", "")
    limit = tool_input.get("limit", 5)
    department = tool_input.get("department")  # 선택적: 학과별 검색
    
    # MCP 호출 시 department 포함
    mcp_args = {
        "query": query,
        "limit": limit
    }
    if department:
        # DB에서 Department 조회하여 code 가져오기
        db = SessionLocal()
        try:
            dept = db.query(models.Department).filter(
                (models.Department.name == department) |
                (models.Department.code == department)
            ).first()
            if dept:
                mcp_args["department"] = dept.code
        finally:
            db.close()
    
    result = await mcp_client.call_tool("notice", "search_notices", mcp_args)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}


async def _handle_get_latest_notices(tool_input: dict, current_user: Optional[models.User] = None):
    """최신 공지사항 조회 (학과별)"""
    
    # 사용자 학과 가져오기
    department = tool_input.get("department")
    if not department and current_user:
        department = current_user.department
    if not department:
        department = "소프트웨어융합학과"  # 기본값
    
    limit = tool_input.get("limit", 5)
    
    # DB에서 Department 조회 (name 또는 code로 검색)
    db = SessionLocal()
    try:
        dept = db.query(models.Department).filter(
            (models.Department.name == department) |
            (models.Department.code == department)
        ).first()
        
        if not dept:
            return {
                "error": f"미등록 학과: {department}",
                "notices": [],
                "message": f"데이터베이스에 '{department}' 학과가 등록되어있지 않습니다."
            }
        
        source = dept.code
    finally:
        db.close()
    
    # 먼저 크롤링 시도 (실패해도 계속 진행)
    try:
        log.debug("공지사항 크롤링 시도: %s", department)
        crawl_result = await mcp_client.call_tool("notice", "crawl_fresh_notices", {
            "department": department,
            "limit": 20
        })
        if isinstance(crawl_result, dict) and crawl_result.get("crawled", 0) > 0:
            log.info("크롤링 성공: %s개 수집", crawl_result.get("crawled"))
        else:
            log.info("크롤링 실패/신규 없음 - DB 기존 데이터 사용")
    except Exception as e:
        log.warning("크롤링 예외 발생 (DB 데이터로 대체): %s", e)
    
    # DB에서 조회
    result = await mcp_client.call_tool("notice", "get_latest_notices", {
        "department": department,
        "source": source,
        "limit": limit
    })
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}


async def _handle_crawl_fresh_notices(tool_input: dict):
    # department 우선, 없으면 source 값을 department로 간주
    department = tool_input.get("department") or tool_input.get("source") or "소프트웨어융합학과"
    limit = tool_input.get("limit", 20)
    keyword = tool_input.get("keyword")  # 새로 추가: 키워드 필터링
    
    # MCP 호출 시 keyword 포함
    mcp_args = {
        "department": department,
        "limit": limit
    }
    if keyword:
        mcp_args["keyword"] = keyword

    # 크롤링은 타임아웃을 짧게 설정하고 실패해도 계속 진행
    result = await mcp_client.call_tool("notice", "crawl_fresh_notices", mcp_args, timeout=5.0)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}


async def _handle_search_meals(tool_input: dict):
    query = tool_input.get("query", "")
    result = await mcp_client.call_tool("meal", "search_meals", {"query": query}, timeout=5.0)
    return {"meals": result}



async def _handle_get_next_shuttle(tool_input: dict):
    route = tool_input.get("route")
    result = await mcp_client.call_tool("shuttle", "get_next_shuttle", {"route": route}, timeout=10.0)
    return {"shuttle": result}


async def _handle_search_courses(tool_input: dict):
    department = tool_input.get("department")
    keyword = tool_input.get("keyword")
    result = await mcp_client.call_tool("course", "search_courses", {
        "department": department,
        "keyword": keyword
        }, timeout=10.0)
    data = json.loads(result) if isinstance(result, str) else result
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_search_curriculum(tool_input: dict):
    query = tool_input.get("query", "")
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool(
        "curriculum",
        "search_curriculum",
        {"query": query, "year": year},
        timeout=10.0,
        retries=0,
    )
    
    data = json.loads(result) if isinstance(result, str) else result
    if not data or not data.get("found"):
        return {"found": False, "message": f"'{query}'에 대한 교과과정 과목이 없습니다."}
    
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_get_curriculum_by_semester(tool_input: dict):
    semester = tool_input.get("semester")
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool(
        "curriculum",
        "get_curriculum_by_semester",
        {"semester": semester, "year": year},
        timeout=5.0,
        retries=0,
    )

    try:
        data = json.loads(result) if isinstance(result, str) else result
    except Exception:
        return {"found": False, "message": "교과과정 데이터를 파싱하지 못했습니다."}

    if not data or not data.get("found"):
        return {"found": False, "message": data.get("error") or f"{semester}에 개설되는 과목이 없습니다."}
    
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_list_programs(tool_input: dict):
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool("curriculum", "list_programs", {"year": year}, timeout=10.0)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"found": True, "programs": data.get("programs", [])}


async def _handle_get_requirements(tool_input: dict, current_user: Optional[models.User]):
    """
    졸업요건 조회 - 사용자 정보 자동 활용
    
    로그인된 사용자의 경우:
    - program이 비어있으면 current_user.department에서 자동 추출
    - year가 비어있으면 current_user.admission_year 사용
    """
    program = tool_input.get("program")
    year = tool_input.get("year")
    
    # 학과명 → 프로그램 코드 매핑 (확장 가능)
    dept_map = {
        "컴퓨터공학과": "KHU-CSE",
        "컴퓨터공학부": "KHU-CSE",
        "소프트웨어융합학과": "KHU-SW",
        "인공지능학과": "KHU-AI",
        "전자공학과": "KHU-ECE",
        "산업경영공학과": "KHU-IME"
    }
    
    # 사용자 정보 우선 사용
    if current_user:
        if not program:
            program = dept_map.get(current_user.department, "KHU-CSE")
            log.info("사용자 학과(%s) -> 프로그램(%s)", current_user.department, program)

        if not year:
            year = str(current_user.admission_year)
            log.info("사용자 입학년도(%s) 적용", current_user.admission_year)

    # 기본값 설정 (사용자 미로그인 또는 학과 미매핑)
    if not program:
        program = "KHU-CSE"
    if not year:
        year = "latest"

    try:
        log.debug("MCP call: get_requirements(program=%s, year=%s, user=%s)", program, year, current_user.student_id if current_user else "anonymous")
        
        result = await mcp_client.call_tool(
            "curriculum",
            "get_requirements",
            {"program": program, "year": year},
            timeout=10.0,
            retries=2,
        )
        
        if result is None:
            return {"found": False, "error": "Curriculum MCP 서버 응답 없음"}
        
        data = json.loads(result) if isinstance(result, str) else result
        if data is None:
            return {"found": False, "error": "졸업요건 데이터를 찾을 수 없습니다"}
        
        if isinstance(data, dict) and data.get("error"):
            return {"found": False, "error": data}
        
        log.info("졸업요건 조회 성공: %s %s학번", program, year)
        return {"found": True, "requirements": data}

    except Exception as e:
        log.error("get_requirements 에러: %s", e)
        return {"found": False, "error": f"졸업요건 조회 실패: {str(e)}"}


async def _handle_evaluate_progress(tool_input: dict, current_user: Optional[models.User]):
    """
    졸업요건 진행도 평가 - 사용자 정보 자동 활용
    
    로그인된 사용자의 경우:
    - program이 비어있으면 current_user.department에서 자동 추출
    - year가 비어있으면 current_user.admission_year 사용
    """
    program = tool_input.get("program")
    year = tool_input.get("year")
    taken_courses = tool_input.get("taken_courses", [])
    
    # 학과명 → 프로그램 코드 매핑
    dept_map = {
        "컴퓨터공학과": "KHU-CSE",
        "컴퓨터공학부": "KHU-CSE",
        "소프트웨어융합학과": "KHU-SW",
        "인공지능학과": "KHU-AI",
        "전자공학과": "KHU-ECE",
        "산업경영공학과": "KHU-IME"
    }
    
    # 사용자 정보 우선 사용
    if current_user:
        if not program:
            program = dept_map.get(current_user.department, "KHU-CSE")
            log.info("사용자 학과(%s) -> 프로그램(%s)", current_user.department, program)

        if not year:
            year = str(current_user.admission_year)
            log.info("사용자 입학년도(%s) 적용", current_user.admission_year)

    # 기본값 설정
    if not program:
        program = "KHU-CSE"
    if not year:
        year = "latest"

    try:
        log.debug("MCP call: evaluate_progress(program=%s, year=%s, courses=%s개, user=%s)", program, year, len(taken_courses), current_user.student_id if current_user else "anonymous")
        
        result = await mcp_client.call_tool(
            "curriculum",
            "evaluate_progress",
            {"program": program, "year": year, "taken_courses": taken_courses},
            timeout=10.0,
            retries=2,
        )
        
        if result is None:
            return {"found": False, "error": "Curriculum MCP 서버 응답 없음"}
        
        data = json.loads(result) if isinstance(result, str) else result
        if data is None:
            return {"found": False, "error": "졸업요건 평가 데이터를 찾을 수 없습니다"}
        
        if isinstance(data, dict) and data.get("error"):
            return {"found": False, "error": data}
        
        log.info("진행도 평가 완료: %s %s학번", program, year)
        return {"found": True, "evaluation": data}

    except Exception as e:
        log.error("evaluate_progress 에러: %s", e)
        return {"found": False, "error": f"졸업요건 평가 실패: {str(e)}"}


async def _handle_get_library_info(tool_input: dict):
    result = await mcp_client.call_tool("library", "get_library_info", tool_input, timeout=5.0)
    data = json.loads(result) if isinstance(result, str) else result
    return {
        "library_info": data,
        "library_reservation_url": "https://library.khu.ac.kr/seat",
        "show_reservation_button": True,
        "message": "도서관 좌석 현황을 확인하려면 도서관 예약 시스템에 로그인하세요."
    }



async def _handle_get_seat_availability(tool_input: dict, library_username: Optional[str], library_password: Optional[str], current_user: Optional[models.User]):
    # 자격 증명 없으면 캐시에서 조회
    if not library_username or not library_password:
        try:
            from ..cache import cache_manager
            await cache_manager.connect()
            cache_key = None
            # current_user 정보가 없는 경우 tool_input에 student_id가 들어있을 수 있어 보강
            student_id = tool_input.get("student_id") or (current_user.student_id if current_user else None)
            # cache_manager에는 로그인 시 student_id로 저장
            if student_id:
                cache_key = f"library:cred:{student_id}"
            # 그래도 없으면 실패 응답
            if cache_key:
                cached = await cache_manager.get(cache_key)
                if cached:
                    library_username = cached.get("username")
                    library_password = cached.get("password")
        except Exception as e:
            log.warning("library cred cache 조회 실패: %s", e)

    if not library_username or not library_password:
        return {"needs_login": True, "message": "도서관 로그인을 위해 학번과 비밀번호가 필요합니다."}
    
    result = await mcp_client.call_tool("library", "get_seat_availability", {
        **tool_input,
        "username": library_username,
        "password": library_password
    }, timeout=5.0)
    return {"library_seats": json.loads(result) if isinstance(result, str) else result}


async def _handle_reserve_seat(tool_input: dict, library_username: Optional[str], library_password: Optional[str], current_user: Optional[models.User]):
    if not library_username or not library_password:
        return {"needs_login": True, "message": "학번과 비밀번호가 필요합니다."}
    
    result = await mcp_client.call_tool("library", "reserve_seat", {
        **tool_input,
        "username": library_username,
        "password": library_password
    }, timeout=5.0)
    return {"reservation": json.loads(result) if isinstance(result, str) else result}


async def _handle_get_today_meal(tool_input: dict):
    meal_type = tool_input.get("meal_type", "lunch")
    try:
        result = await mcp_client.call_tool("meal", "get_today_meal", {"meal_type": meal_type}, timeout=5.0)
        parsed = json.loads(result) if isinstance(result, str) else result
        
        # 에러 응답인 경우 빈 배열 반환
        if "error" in parsed or not parsed.get("success", True):
            error_msg = parsed.get("message", parsed.get("error", "알 수 없는 오류"))
            return {"meals": [], "error_message": f"학식 조회 실패: {error_msg}"}
        
        # 정상 응답: MealInfo 스키마에 맞게 변환
        meal_info = {
            "cafeteria": parsed.get("cafeteria", "학생회관 학생식당"),
            "meal_type": parsed.get("meal_type", meal_type),
            "menu": parsed.get("menu") or "메뉴 정보 없음",
            "price": parsed.get("price") or 5000,
            "menu_url": parsed.get("menu_url"),
            "source_url": parsed.get("source_url")
        }
        return {"meals": [meal_info]}
    except Exception as e:
        log.error("get_today_meal 에러: %s", e)
        return {"meals": [], "error_message": f"학식 조회 중 오류: {str(e)}"}


async def _handle_get_cafeteria_info():
    result = await mcp_client.call_tool("meal", "get_cafeteria_info", {}, timeout=5.0)
    return {"cafeteria": json.loads(result) if isinstance(result, str) else result}
