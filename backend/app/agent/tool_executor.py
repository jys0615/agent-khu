"""
Tool 실행 핸들러
"""
import json
from typing import Optional, Any, Dict
from ..mcp_client import mcp_client
from .. import models
from ..database import SessionLocal


async def process_tool_call(
    tool_name: str,
    tool_input: dict,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    library_password: Optional[str] = None,
    current_user: Optional[models.User] = None
) -> Dict[str, Any]:
    """Tool 호출 처리"""
    try:
        if tool_name == "search_classroom":
            return await _handle_search_classroom(tool_input, user_latitude, user_longitude)
        
        elif tool_name == "search_notices":
            return await _handle_search_notices(tool_input)
        
        elif tool_name == "get_latest_notices":
            return await _handle_get_latest_notices(tool_input)
        
        elif tool_name == "crawl_fresh_notices":
            return await _handle_crawl_fresh_notices(tool_input)
        
        elif tool_name == "search_meals":
            return await _handle_search_meals(tool_input)
        
        elif tool_name == "get_next_shuttle":
            return await _handle_get_next_shuttle(tool_input)
        
        elif tool_name == "search_courses":
            return await _handle_search_courses(tool_input)
        
        elif tool_name == "search_curriculum":
            return await _handle_search_curriculum(tool_input)
        
        elif tool_name == "get_curriculum_by_semester":
            return await _handle_get_curriculum_by_semester(tool_input)
        
        elif tool_name == "list_programs":
            return await _handle_list_programs(tool_input)
        
        elif tool_name == "get_requirements":
            return await _handle_get_requirements(tool_input, current_user)
        
        elif tool_name == "evaluate_progress":
            return await _handle_evaluate_progress(tool_input, current_user)
        
        elif tool_name == "get_library_info":
            return await _handle_get_library_info(tool_input)
        
        elif tool_name == "get_seat_availability":
            return await _handle_get_seat_availability(tool_input, library_username, library_password)
        
        elif tool_name == "reserve_seat":
            return await _handle_reserve_seat(tool_input, library_username, library_password)
        
        elif tool_name == "get_today_meal":
            return await _handle_get_today_meal(tool_input)
        
        elif tool_name == "get_cafeteria_info":
            return await _handle_get_cafeteria_info()
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        print(f"❌ Tool 실행 에러: {e}")
        return {"error": str(e)}


async def _handle_search_classroom(tool_input: dict, user_latitude: Optional[float], user_longitude: Optional[float]):
    query = tool_input.get("query", "")
    
    # 🔍 디버그 로그 추가
    print(f"🔍 DEBUG - MCP Raw Result 호출 전")
    
    result = await mcp_client.call_tool("classroom", "search_classroom", {"query": query})
    
    # 🔍 디버그 로그 추가
    print(f"🔍 DEBUG - MCP Raw Result: {result}")
    print(f"🔍 DEBUG - Result Type: {type(result)}")
    
    data = json.loads(result) if isinstance(result, str) else result
    
    print(f"🔍 DEBUG - Parsed Data: {data}")
    print(f"🔍 DEBUG - Found: {data.get('found')}")
    
    if not data or not data.get("found"):
        return {"message": f"'{query}'에 대한 검색 결과가 없습니다."}
    
    room = data["rooms"][0]
    map_link = None
    if user_latitude and user_longitude and room.get("latitude") and room.get("longitude"):
        map_link = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={user_latitude},{user_longitude}"
            f"&destination={room['latitude']},{room['longitude']}"
        )
    
    return {
        "classroom": {
            "code": room.get("code", ""),
            "building_name": room.get("building", ""),
            "room_number": room.get("room_number", ""),
            "floor": room.get("floor", ""),
            "room_name": room.get("name", ""),
            "room_type": room.get("room_type", "classroom"),
            "professor_name": room.get("professor_name"),
            "is_accessible": room.get("is_accessible", True),
            "latitude": room.get("latitude"),
            "longitude": room.get("longitude")
        },
        "map_link": map_link
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
        print(f"🔄 공지사항 크롤링 시도: {department}")
        crawl_result = await mcp_client.call_tool("notice", "crawl_fresh_notices", {
            "department": department,
            "limit": 20
        })
        if isinstance(crawl_result, dict) and crawl_result.get("crawled", 0) > 0:
            print(f"✅ 크롤링 성공: {crawl_result.get('crawled')}개 수집")
        else:
            print(f"ℹ️ 크롤링 실패/신규 없음 - DB 기존 데이터 사용")
    except Exception as e:
        print(f"⚠️ 크롤링 예외 발생 (DB 데이터로 대체): {e}")
    
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
    
    result = await mcp_client.call_tool("notice", "crawl_fresh_notices", mcp_args)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}


async def _handle_search_meals(tool_input: dict):
    query = tool_input.get("query", "")
    result = await mcp_client.call_tool("meal", "search_meals", {"query": query})
    return {"meals": result}



async def _handle_get_next_shuttle(tool_input: dict):
    route = tool_input.get("route")
    result = await mcp_client.call_tool("shuttle", "get_next_shuttle", {"route": route})
    return {"shuttle": result}


async def _handle_search_courses(tool_input: dict):
    department = tool_input.get("department")
    keyword = tool_input.get("keyword")
    result = await mcp_client.call_tool("course", "search_courses", {
        "department": department,
        "keyword": keyword
    })
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_search_curriculum(tool_input: dict):
    query = tool_input.get("query", "")
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool("curriculum", "search_curriculum", {"query": query, "year": year})
    
    data = json.loads(result) if isinstance(result, str) else result
    if not data or not data.get("found"):
        return {"found": False, "message": f"'{query}'에 대한 교과과정 과목이 없습니다."}
    
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_get_curriculum_by_semester(tool_input: dict):
    semester = tool_input.get("semester")
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool("curriculum", "search_curriculum", {"query": semester, "year": year})
    
    data = json.loads(result) if isinstance(result, str) else result
    if not data or not data.get("found"):
        return {"found": False, "message": f"{semester}에 개설되는 과목이 없습니다."}
    
    return {"found": True, "courses": data.get("courses", [])}


async def _handle_list_programs(tool_input: dict):
    year = tool_input.get("year", "latest")
    result = await mcp_client.call_tool("curriculum", "list_programs", {"year": year})
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"found": True, "programs": data.get("programs", [])}


async def _handle_get_requirements(tool_input: dict, current_user: Optional[models.User]):
    program = tool_input.get("program")
    year = tool_input.get("year")
    
    if current_user:
        if not program:
            dept_map = {
                "컴퓨터공학부": "KHU-CSE",
                "소프트웨어융합학과": "KHU-SW",
                "인공지능학과": "KHU-AI"
            }
            program = dept_map.get(current_user.department, "KHU-CSE")
        
        if not year:
            year = str(current_user.admission_year)
    
    try:
        result = await mcp_client.call_tool("curriculum", "get_requirements", {
            "program": program,
            "year": year
        })
        
        if result is None:
            return {"found": False, "error": "Curriculum MCP 서버 응답 없음"}
        
        data = json.loads(result) if isinstance(result, str) else result
        if data is None:
            return {"found": False, "error": "졸업요건 데이터를 찾을 수 없습니다"}
        
        if isinstance(data, dict) and data.get("error"):
            return {"found": False, "error": data}
        
        return {"found": True, "requirements": data}
    
    except Exception as e:
        print(f"❌ get_requirements 에러: {e}")
        return {"found": False, "error": f"졸업요건 조회 실패: {str(e)}"}


async def _handle_evaluate_progress(tool_input: dict, current_user: Optional[models.User]):
    program = tool_input.get("program")
    year = tool_input.get("year")
    taken = tool_input.get("taken_courses", [])
    
    if current_user:
        if not program:
            dept_map = {
                "컴퓨터공학부": "KHU-CSE",
                "소프트웨어융합학과": "KHU-SW",
                "인공지능학과": "KHU-AI"
            }
            program = dept_map.get(current_user.department, "KHU-CSE")
        
        if not year:
            year = str(current_user.admission_year)
    
    try:
        result = await mcp_client.call_tool("curriculum", "evaluate_progress", {
            "program": program,
            "year": year,
            "taken_courses": taken
        })
        
        if result is None:
            return {"found": False, "error": "Curriculum MCP 서버 응답 없음"}
        
        data = json.loads(result) if isinstance(result, str) else result
        if data is None:
            return {"found": False, "error": "졸업요건 평가 데이터를 찾을 수 없습니다"}
        
        if isinstance(data, dict) and data.get("error"):
            return {"found": False, "error": data}
        
        return {"found": True, "evaluation": data}
    
    except Exception as e:
        print(f"❌ evaluate_progress 에러: {e}")
        return {"found": False, "error": f"졸업요건 평가 실패: {str(e)}"}


async def _handle_get_library_info(tool_input: dict):
    result = await mcp_client.call_tool("library", "get_library_info", tool_input)
    data = json.loads(result) if isinstance(result, str) else result
    return {
        "library_info": data,
        "library_reservation_url": "https://library.khu.ac.kr/seat",
        "show_reservation_button": True,
        "message": "도서관 좌석 현황을 확인하려면 도서관 예약 시스템에 로그인하세요."
    }



async def _handle_get_seat_availability(tool_input: dict, library_username: Optional[str], library_password: Optional[str]):
    if not library_username or not library_password:
        return {"needs_login": True, "message": "학번과 비밀번호가 필요합니다."}
    
    result = await mcp_client.call_tool("library", "get_seat_availability", {
        **tool_input,
        "username": library_username,
        "password": library_password
    })
    return {"library_seats": json.loads(result) if isinstance(result, str) else result}


async def _handle_reserve_seat(tool_input: dict, library_username: Optional[str], library_password: Optional[str]):
    if not library_username or not library_password:
        return {"needs_login": True, "message": "학번과 비밀번호가 필요합니다."}
    
    result = await mcp_client.call_tool("library", "reserve_seat", {
        **tool_input,
        "username": library_username,
        "password": library_password
    })
    return {"reservation": json.loads(result) if isinstance(result, str) else result}


async def _handle_get_today_meal(tool_input: dict):
    meal_type = tool_input.get("meal_type", "lunch")
    result = await mcp_client.call_tool("meal", "get_today_meal", {"meal_type": meal_type})
    return {"meals": json.loads(result) if isinstance(result, str) else result}


async def _handle_get_cafeteria_info():
    result = await mcp_client.call_tool("meal", "get_cafeteria_info", {})
    return {"cafeteria": json.loads(result) if isinstance(result, str) else result}
