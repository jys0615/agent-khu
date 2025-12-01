"""
Claude + MCP 기반 자율 AI Agent (캐싱 최적화)
"""
import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from anthropic import Anthropic
from . import models
from . import schemas
from .mcp_client import mcp_client
from .cache import cache_manager

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 캐시 TTL 설정 (초 단위)
CACHE_TTL = {
    "search_classroom": int(os.getenv("CACHE_TTL_CLASSROOM", "86400")),  # 24시간
    "search_notices": int(os.getenv("CACHE_TTL_NOTICE", "3600")),        # 1시간
    "get_latest_notices": int(os.getenv("CACHE_TTL_NOTICE", "3600")),    # 1시간
    "search_curriculum": int(os.getenv("CACHE_TTL_CURRICULUM", "86400")), # 24시간
    "get_curriculum_by_semester": int(os.getenv("CACHE_TTL_CURRICULUM", "86400")),
    "list_programs": int(os.getenv("CACHE_TTL_CURRICULUM", "86400")),
    "get_requirements": int(os.getenv("CACHE_TTL_CURRICULUM", "86400")),
    "get_library_info": int(os.getenv("CACHE_TTL_LIBRARY", "300")),      # 5분
    "get_next_shuttle": 180,  # 3분 (셔틀 시간표)
    "get_cafeteria_info": 86400,  # 24시간
}

# Tools 정의
tools = [
    {
        "name": "search_classroom",
        "description": "경희대 전자정보대학관 강의실/연구실/편의시설을 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색어 (강의실 번호, 교수명, 시설명 등)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_notices",
        "description": "학과 공지사항을 키워드로 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색 키워드"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "결과 개수"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_latest_notices",
        "description": "최신 공지사항을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "공지 출처",
                    "enum": ["swedu", "department"],
                    "default": "swedu"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "결과 개수"
                }
            }
        }
    },
    {
        "name": "crawl_fresh_notices",
        "description": "실시간으로 공지사항을 크롤링합니다 (최신 정보 필요 시)",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": ["swedu", "department"],
                    "default": "swedu"
                },
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            }
        }
    },
    # {
    #     "name": "get_today_meal",
    #     "description": "오늘의 학식 메뉴를 조회합니다",
    #     "input_schema": {"type": "object", "properties": {
    #         "cafeteria": {"type": "string", "enum": ["student", "faculty", "dormitory"]}
    #     }}
    # },
    {
        "name": "search_meals",
        "description": "특정 메뉴가 나오는 날을 검색합니다",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "검색할 메뉴"}
        }, "required": ["query"]}
    },
    {
        "name": "get_seat_status",
        "description": "도서관 좌석 현황을 조회합니다",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "find_available_seats",
        "description": "빈 자리가 있는 열람실을 찾습니다",
        "input_schema": {"type": "object", "properties": {
            "min_seats": {"type": "integer", "default": 1}
        }}
    },
    {
        "name": "get_next_shuttle",
        "description": "다음 셔틀버스 시간을 조회합니다",
        "input_schema": {"type": "object", "properties": {
            "route": {"type": "string", "enum": ["to_station", "to_campus"]}
        }}
    },
    {
        "name": "search_courses",
        "description": "학과별 개설 교과목을 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "학과명 (예: 소프트웨어융합학과)"
                },
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (과목명, 교수명)"
                }
            }
        }
    },
    {
        "name": "search_curriculum",
        "description": "소프트웨어융합대학 교과과정에서 과목을 검색합니다 (과목명, 과목코드, 학점, 선수과목)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 과목명 또는 과목코드 (예: 자료구조, SWE2001)"
                },
                "year": {
                    "type": "string",
                    "description": "학년도 (선택사항, 기본값: latest)",
                    "default": "latest"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_curriculum_by_semester",
        "description": "특정 학기에 개설되는 교과과정 과목 목록을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "semester": {
                    "type": "string",
                    "description": "학기 (1학기 또는 2학기)",
                    "enum": ["1학기", "2학기"]
                },
                "year": {
                    "type": "string",
                    "description": "학년도 (선택사항)",
                    "default": "latest"
                }
            },
            "required": ["semester"]
        }
    },
    {
        "name": "list_programs",
        "description": "해당 연도의 전공 코드 목록(KHU-CSE, KHU-SW, KHU-AI 등)을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "string", "description": "학년도", "default": "latest"}
            }
        }
    },
    {
        "name": "get_requirements",
        "description": "전공/연도별 졸업요건(그룹/최소학점/정책)을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "description": "전공 코드 (예: KHU-CSE)"},
                "year": {"type": "string", "description": "학년도"}
            },
            "required": ["program", "year"]
        }
    },
    {
        "name": "evaluate_progress",
        "description": "수강내역 기준 졸업요건 충족도를 평가합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "description": "전공 코드"},
                "year": {"type": "string", "description": "학년도"},
                "taken_courses": {"type": "array", "items": {"type": "string"}, "description": "이수 과목 코드 목록"}
            },
            "required": ["program", "year", "taken_courses"]
        }
    },
    {
        "name": "get_library_info",
        "description": "경희대 도서관 기본 정보 조회 (로그인 불필요). 운영시간, 연락처, 층별 안내 등",
        "input_schema": {
            "type": "object",
            "properties": {
                "campus": {
                    "type": "string",
                    "enum": ["seoul", "global"],
                    "description": "캠퍼스 (seoul: 서울캠퍼스, global: 국제캠퍼스)"
                }
            }
        }
    },
    {
        "name": "get_seat_availability",
        "description": "경희대 도서관 실시간 좌석 현황 조회 (로그인 필요). 사용자로부터 학번과 비밀번호를 받은 경우에만 호출",
        "input_schema": {
            "type": "object",
            "properties": {
                "campus": {
                    "type": "string",
                    "description": "캠퍼스 (seoul/global)"
                }
            }
        }
    },
    {
        "name": "reserve_seat",
        "description": "경희대 도서관 좌석 예약 (로그인 필요)",
        "input_schema": {
            "type": "object",
            "properties": {
                "room": {"type": "string", "description": "열람실 이름"},
                "seat_number": {"type": "string", "description": "좌석 번호"}
            },
            "required": ["room"]
        }
    },
     {
        "name": "get_today_meal",
        "description": "오늘의 학식 메뉴를 조회합니다 (Vision API로 식단표 이미지 분석)",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_type": {
                    "type": "string",
                    "enum": ["lunch", "dinner"],
                    "default": "lunch",
                    "description": "식사 시간 (중식/석식)"
                }
            }
        }
    },
    {
        "name": "get_cafeteria_info",
        "description": "학생회관 식당 기본 정보를 조회합니다 (위치, 운영시간, 가격)",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]


def detect_curriculum_intent(message: str) -> dict:
    """메시지에서 교과과정 관련 의도 감지"""
    msg_lower = message.lower()
    
    if any(kw in msg_lower for kw in ["졸업", "요건", "조건", "학점", "이수"]):
        if any(kw in msg_lower for kw in ["현황", "평가", "진행", "확인", "충족"]):
            return {"intent": "progress", "keywords": ["progress", "evaluate"]}
        return {"intent": "requirements", "keywords": ["requirements", "졸업요건"]}
    
    if any(kw in msg_lower for kw in ["학기", "개설", "몇학기"]):
        return {"intent": "semester", "keywords": ["semester", "개설"]}
    
    if any(kw in msg_lower for kw in ["과목", "수업", "강의", "코드"]):
        return {"intent": "course_search", "keywords": ["search", "과목"]}
    
    return {"intent": None}


async def process_tool_call_async(
    tool_name: str,
    tool_input: dict,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    current_user: Optional[models.User] = None,
    library_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool 호출 실행 (MCP 서버 연동) - 캐싱 최적화
    """
    if tool_input is None:
        tool_input = {}
    
    # 캐시 가능한 tool인지 확인
    if tool_name in CACHE_TTL:
        # 캐시 키 생성 (tool_name + input의 정렬된 JSON)
        cache_key_base = f"tool:{tool_name}"
        input_str = json.dumps(tool_input, sort_keys=True, ensure_ascii=False)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()[:16]
        cache_key = f"{cache_key_base}:{input_hash}"
        
        # 캐시 조회
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            print(f"✅ 캐시 히트: {tool_name}")
            return cached_result
    
    # 캐시 없음 - 실제 tool 실행
    result = await _execute_tool_internal(
        tool_name, tool_input, user_latitude, user_longitude,
        library_username, current_user, library_password
    )
    
    # 캐시 저장
    if tool_name in CACHE_TTL and result and not result.get("error"):
        ttl = CACHE_TTL[tool_name]
        await cache_manager.set(cache_key, result, ttl=ttl)
        print(f"✅ 캐시 저장: {tool_name} (TTL: {ttl}초)")
    
    return result


async def _execute_tool_internal(
    tool_name: str,
    tool_input: dict,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    current_user: Optional[models.User] = None,
    library_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool 실제 실행 로직 (내부 함수)
    """
    try:
        if tool_name == "search_classroom":
            query = tool_input.get("query", "")
            result = await mcp_client.call_tool("classroom", "search_room", {"query": query})
            
            try:
                data = json.loads(result) if isinstance(result, str) else result
            except:
                return {"error": "Failed to parse response"}
            
            if not data or not data.get("found"):
                return {"message": f"'{query}'에 대한 검색 결과가 없습니다."}
            
            room = data["rooms"][0]
            
            # Map 링크 생성
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
        
        elif tool_name == "search_notices":
            query = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            result = await mcp_client.call_tool("notice", "search_notices", {"query": query, "limit": limit})
            
            try:
                data = json.loads(result) if isinstance(result, str) else result
            except:
                return {"error": "Failed to parse response"}
            
            if not data or not data.get("notices"):
                return {"message": f"'{query}'에 대한 공지사항이 없습니다."}
            
            return {"notices": data["notices"]}
        
        elif tool_name == "get_latest_notices":
            source = tool_input.get("source", "swedu")
            limit = tool_input.get("limit", 5)
            result = await mcp_client.call_tool("notice", "get_latest_notices", {"source": source, "limit": limit})
            
            try:
                data = json.loads(result) if isinstance(result, str) else result
            except:
                return {"error": "Failed to parse response"}
            
            return {"notices": data.get("notices", [])}
        
        elif tool_name == "crawl_fresh_notices":
            source = tool_input.get("source", "swedu")
            limit = tool_input.get("limit", 20)
            result = await mcp_client.call_tool("notice", "crawl_fresh_notices", {"source": source, "limit": limit})
            
            try:
                data = json.loads(result) if isinstance(result, str) else result
            except:
                return {"error": "Failed to parse response"}
            
            return {"notices": data.get("notices", [])}
        
        elif tool_name == "get_today_meal":
            cafeteria = tool_input.get("cafeteria", "student")
            result = await mcp_client.call_tool("meal", "get_today_meal", {"cafeteria": cafeteria})
            return {"meals": result}
        
        elif tool_name == "search_meals":
            query = tool_input.get("query", "")
            result = await mcp_client.call_tool("meal", "search_meals", {"query": query})
            return {"meals": result}
        
        elif tool_name == "get_seat_status":
            result = await mcp_client.call_tool("library", "get_seat_status", {})
            
            # 도서관 예약 링크 추가
            return {
                "seats": result,
                "library_reservation_url": "https://library.khu.ac.kr/seat",
                "show_reservation_button": True
            }
        
        elif tool_name == "find_available_seats":
            min_seats = tool_input.get("min_seats", 1)
            result = await mcp_client.call_tool("library", "find_available_seats", {"min_seats": min_seats})
            
            # 도서관 예약 링크 추가
            return {
                "seats": result,
                "library_reservation_url": "https://library.khu.ac.kr/seat",
                "show_reservation_button": True
            }
        
        elif tool_name == "get_next_shuttle":
            route = tool_input.get("route")
            result = await mcp_client.call_tool("shuttle", "get_next_shuttle", {"route": route})
            return {"shuttle": result}
        
        elif tool_name == "search_courses":
            department = tool_input.get("department")
            keyword = tool_input.get("keyword")
            result = await mcp_client.call_tool("course", "search_courses", {
                "department": department,
                "keyword": keyword
            })
            
            try:
                data = json.loads(result) if isinstance(result, str) else result
            except:
                return {"error": "Failed to parse course search response"}
            
            if not data or not data.get("courses"):
                return {"message": "검색 결과가 없습니다."}
            
            return {"courses": data["courses"]}
        
        elif tool_name == "search_curriculum":
            query = tool_input.get("query", "")
            year = tool_input.get("year", "latest")
            result = await mcp_client.call_tool("curriculum", "search_courses", {"query": query, "year": year})
            data = json.loads(result) if isinstance(result, str) else result
            if not data or not data.get("found"):
                return {"found": False, "message": f"'{query}'에 대한 교과과정 과목이 없습니다."}
            return {"found": True, "courses": data.get("courses", [])}
        
        elif tool_name == "get_curriculum_by_semester":
            semester = tool_input.get("semester")
            year = tool_input.get("year", "latest")
            result = await mcp_client.call_tool("curriculum", "search_courses", {"query": semester, "year": year})
            data = json.loads(result) if isinstance(result, str) else result
            if not data or not data.get("found"):
                return {"found": False, "message": f"{semester}에 개설되는 과목이 없습니다."}
            return {"found": True, "courses": data.get("courses", [])}
        
        elif tool_name == "list_programs":
            year = tool_input.get("year", "latest")
            result = await mcp_client.call_tool("curriculum", "list_programs", {"year": year})
            data = json.loads(result) if isinstance(result, str) else result
            return {"found": True, "programs": data.get("programs", [])}
        
        elif tool_name == "get_requirements":
            program = tool_input.get("program")
            year = tool_input.get("year")
            
            # 사용자 정보로 기본값 설정
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
            
            print(f"🔍 get_requirements 호출: program={program}, year={year}")
            
            try:
                result = await mcp_client.call_tool("curriculum", "get_requirements", {
                    "program": program, 
                    "year": year
                })
                
                # 🔧 안전한 파싱
                if result is None:
                    return {
                        "found": False, 
                        "error": "Curriculum MCP 서버 응답 없음"
                    }
                
                data = json.loads(result) if isinstance(result, str) else result
                
                # 🔧 data가 None인 경우 처리
                if data is None:
                    return {
                        "found": False,
                        "error": "졸업요건 데이터를 찾을 수 없습니다"
                    }
                
                # dict이고 error가 있는 경우
                if isinstance(data, dict) and data.get("error"):
                    return {"found": False, "error": data}
                
                return {"found": True, "requirements": data}
                
            except Exception as e:
                print(f"❌ get_requirements 에러: {e}")
                return {
                    "found": False,
                    "error": f"졸업요건 조회 실패: {str(e)}"
                }
        
        elif tool_name == "evaluate_progress":
            program = tool_input.get("program")
            year = tool_input.get("year")
            taken = tool_input.get("taken_courses", [])
            
            # 사용자 정보로 기본값 설정
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
                
                # 🔧 안전한 파싱
                if result is None:
                    return {
                        "found": False,
                        "error": "Curriculum MCP 서버 응답 없음"
                    }
                
                data = json.loads(result) if isinstance(result, str) else result
                
                if data is None:
                    return {
                        "found": False,
                        "error": "졸업요건 평가 데이터를 찾을 수 없습니다"
                    }
                
                if isinstance(data, dict) and data.get("error"):
                    return {"found": False, "error": data}
                
                return {"found": True, "evaluation": data}
                
            except Exception as e:
                print(f"❌ evaluate_progress 에러: {e}")
                return {
                    "found": False,
                    "error": f"졸업요건 평가 실패: {str(e)}"
                }
        
        elif tool_name == "get_library_info":
            result = await mcp_client.call_tool("library", "get_library_info", tool_input)
            return {"library_info": json.loads(result) if isinstance(result, str) else result}
        
        elif tool_name == "get_seat_availability":
            # 🆕 로그인 정보가 있는 경우에만 호출
            if not library_username or not library_password:
                return {"needs_login": True, "message": "학번과 비밀번호가 필요합니다."}
            
            # Tool input에 campus만 있고, username/password는 별도 전달
            campus = tool_input.get("campus", "global")
            result = await mcp_client.call_tool("library", "get_seat_availability", {
                "username": library_username,
                "password": library_password,
                "campus": campus
            })
            return {"library_seats": json.loads(result) if isinstance(result, str) else result}
        
        elif tool_name == "reserve_seat":
            # 🆕 로그인 정보가 있는 경우에만 호출
            if not library_username or not library_password:
                return {"needs_login": True, "message": "학번과 비밀번호가 필요합니다."}
            
            result = await mcp_client.call_tool("library", "reserve_seat", {
                "username": library_username,
                "password": library_password,
                "room": tool_input.get("room"),
                "seat_number": tool_input.get("seat_number")
            })
            return {"reservation": json.loads(result) if isinstance(result, str) else result}
        # agent.py의 process_tool_call_async 함수에 추가할 내용
        # 👇 get_next_shuttle 처리 다음에 삽입

        elif tool_name == "get_today_meal":
            # 오늘의 학식 메뉴 조회 (Vision API)
            meal_type = tool_input.get("meal_type", "lunch")
            
            try:
                result = await mcp_client.call_tool("meal", "get_today_meal", {"meal_type": meal_type})
                
                # 결과 파싱
                try:
                    data = json.loads(result) if isinstance(result, str) else result
                except:
                    data = result
                
                # 에러 처리
                if data.get("error"):
                    return {
                        "error": data.get("error"),
                        "message": data.get("message", "식단 조회에 실패했습니다")
                    }
                
                # 메뉴가 없는 경우
                if not data.get("available") or not data.get("menu"):
                    meal_type_kr = "중식" if meal_type == "lunch" else "석식"
                    return {
                        "message": f"오늘은 {meal_type_kr} 메뉴가 제공되지 않습니다.",
                        "cafeteria": data.get("cafeteria", "학생회관 학생식당"),
                        "location": data.get("location", "학생회관 1층")
                    }
                
                # 정상 응답
                return {
                    "meal": {
                        "date": data.get("date"),
                        "day": data.get("day"),
                        "meal_type": "중식" if meal_type == "lunch" else "석식",
                        "menu": data.get("menu"),
                        "price": data.get("price"),
                        "cafeteria": data.get("cafeteria", "학생회관 학생식당"),
                        "location": data.get("location", "학생회관 1층"),
                        "hours": data.get("hours")
                    }
                }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "식단 조회 중 오류가 발생했습니다"
                }
        
        elif tool_name == "get_cafeteria_info":
            # 식당 기본 정보 조회
            try:
                result = await mcp_client.call_tool("meal", "get_cafeteria_info", {})
                
                try:
                    data = json.loads(result) if isinstance(result, str) else result
                except:
                    data = result
                
                return {
                    "cafeteria": data.get("cafeteria"),
                    "location": data.get("location"),
                    "campus": data.get("campus"),
                    "hours": data.get("hours"),
                    "price_range": data.get("price_range"),
                    "payment_methods": data.get("payment_methods"),
                    "features": data.get("features"),
                    "menu_url": data.get("menu_url"),
                    "contact": data.get("contact")
                }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "식당 정보 조회 중 오류가 발생했습니다"
                }
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        print(f"❌ MCP Tool 실행 에러: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


async def chat_with_claude_async(
    message: str,
    db,
    user_latitude: float = None,
    user_longitude: float = None,
    library_username: str = None,
    library_password: str = None,
    current_user: Optional[models.User] = None,  # 🆕 추가
) -> Dict[str, Any]:
    """
    Claude 기반 자율 Agent (MCP)
    
    Agent는:
    1. 사용자 질문 분석
    2. 필요한 Tool들을 자율적으로 선택
    3. Tool 실행 결과를 바탕으로 다음 행동 결정
    4. 여러 Tool을 연속 실행 가능
    5. 최종 답변 생성
    """
    
    hint = detect_curriculum_intent(message)
    hint_text = ""
    if hint.get("intent"):
        hint_text = f"\n[HINT] curriculum_intent={hint['intent']} (키워드 감지)\n"

    # 🆕 로그인 정보 제공 여부에 따라 system prompt 조정
    login_status = ""
    if library_username and library_password:
        login_status = "\n[로그인 정보 제공됨] 사용자가 학번/비밀번호를 제공했습니다. get_seat_availability와 reserve_seat을 바로 호출할 수 있습니다.\n"
    else:
        login_status = "\n[로그인 정보 없음] 실시간 좌석 조회나 예약 요청 시, 사용자에게 '학번과 비밀번호를 입력해주세요'라고 안내하세요.\n"

        # 🆕 사용자 프로필 기반 프롬프트 생성
    if current_user:
            # 관심분야 파싱
            interests = []
            if current_user.interests:
                try:
                    interests = json.loads(current_user.interests)
                except:
                    pass
            
            interests_str = ", ".join(interests) if interests else "미설정"
            grade_str = f"{current_user.current_grade}학년" if current_user.current_grade else "학년 미설정"
            
            system_prompt = f"""당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

            🎓 현재 대화 중인 학생 정보:
            - 학번: {current_user.student_id[:4]}학번 (입학년도: {current_user.admission_year})
            - 학과: {current_user.department}
            - 캠퍼스: {current_user.campus}
            - 학년: {grade_str}
            - 이수 학점: {current_user.completed_credits or 0}/130학점
            - 관심 분야: {interests_str}

            📋 중요한 지침:
            1. 학생의 학번({current_user.admission_year}학번)과 학과({current_user.department})에 맞는 졸업 요건을 제공하세요
            2. 학생의 캠퍼스({current_user.campus})에 맞는 정보(건물, 셔틀, 식당)를 제공하세요
            3. 이수 학점({current_user.completed_credits or 0}학점)을 고려하여 답변하세요
            4. 학생의 관심 분야({interests_str})와 관련된 추천을 우선하세요
            5. 친근하게 대화하되 존댓말을 사용하세요

            학생에게 가장 도움이 되는 정보를 제공하세요."""
    else:
        system_prompt = """당신은 경희대학교 소프트웨어융합대학 학생들을 돕는 AI 어시스턴트입니다.

        💡 로그인하시면 학번에 맞는 졸업요건, 수강 추천 등 맞춤형 정보를 제공받으실 수 있습니다.""" + hint_text

    messages = [{"role": "user", "content": message}]
    
    # Agent Loop: 최대 5번 반복 (무한 루프 방지)
    max_iterations = 5
    iteration = 0
    
    accumulated_results = {
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
    }
    
    while iteration < max_iterations:
        iteration += 1
        print(f"🤖 Agent Iteration {iteration}/{max_iterations}")
        
        # Claude API 호출
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            tools=tools
        )
        
        # Tool 사용 여부 확인
        if response.stop_reason == "tool_use":
            tool_results = []
            
            # 모든 Tool 실행
            for content in response.content:
                if content.type == "tool_use":
                    print(f"  🔧 Tool 사용: {content.name}")
                    
                    # MCP Tool 실행
                    result = await process_tool_call_async(
                        content.name,
                        content.input,
                        user_latitude,
                        user_longitude,
                        library_username,
                        library_password
                    )
                    
                    # 로그인 필요 감지
                    if result.get("needs_login"):
                        accumulated_results["needs_library_login"] = True
                    
                    # 결과 누적
                    if "classroom" in result:
                        accumulated_results["classrooms"].append(result["classroom"])
                        if "map_link" in result:
                            accumulated_results["map_links"].append(result["map_link"])
                    
                    if "notices" in result:
                        accumulated_results["notices"].extend(result["notices"])
                    
                    if content.name in ["search_curriculum", "get_curriculum_by_semester"]:
                        if "courses" in result and isinstance(result["courses"], list):
                            accumulated_results["curriculum_courses"].extend(result["courses"])
                    elif "courses" in result and isinstance(result["courses"], list):
                        accumulated_results["courses"].extend(result["courses"])
                    
                    if content.name == "get_requirements" and result.get("found"):
                        accumulated_results["requirements_result"] = result["requirements"]
                    if content.name == "evaluate_progress" and result.get("found"):
                        accumulated_results["progress_result"] = result["evaluation"]
                    
                    if content.name == "get_library_info" and "library_info" in result:
                        accumulated_results["library_info"] = result["library_info"]
                    if content.name == "get_seat_availability" and "library_seats" in result:
                        accumulated_results["library_seats"] = result["library_seats"]
                    if content.name == "reserve_seat" and "reservation" in result:
                        accumulated_results["reservation"] = result["reservation"]
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            
            # 대화 이력 업데이트
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
        elif response.stop_reason == "end_turn":
            print("✅ Agent 작업 완료")
            
            # 최종 응답 추출
            answer = ""
            for content in response.content:
                if content.type == "text":
                    answer += content.text
            
            # 결과 구성
            result = {"message": answer}
            
            if accumulated_results["classrooms"]:
                result["classroom"] = accumulated_results["classrooms"][0]
                result["map_link"] = accumulated_results["map_links"][0] if accumulated_results["map_links"] else None
                result["show_map_button"] = True
            
            if accumulated_results["notices"]:
                result["notices"] = accumulated_results["notices"]
                result["show_notices"] = True
            
            if accumulated_results["courses"]:
                result["courses"] = accumulated_results["courses"]
                result["show_courses"] = True
            
            if accumulated_results["curriculum_courses"]:
                result["curriculum_courses"] = accumulated_results["curriculum_courses"]
                result["show_courses"] = True
            
            if accumulated_results["requirements_result"]:
                result["requirements"] = accumulated_results["requirements_result"]
                result["show_requirements"] = True
            if accumulated_results["progress_result"]:
                result["evaluation"] = accumulated_results["progress_result"]
                result["show_evaluation"] = True
            
            # 🆕 도서관 결과 처리 (좌석 현황이 있으면 기본 정보 숨김)
            if accumulated_results["library_seats"]:
                result["library_seats"] = accumulated_results["library_seats"]
                result["show_library_seats"] = True
                # 좌석 현황이 있으면 기본 정보는 표시 안 함
            elif accumulated_results["library_info"]:
                result["library_info"] = accumulated_results["library_info"]
                result["show_library_info"] = True
            
            if accumulated_results["reservation"]:
                result["reservation"] = accumulated_results["reservation"]
                result["show_reservation"] = True
            if accumulated_results["needs_library_login"]:
                result["needs_library_login"] = True
            
            return result
        
        else:
            print(f"⚠️ Agent 종료: {response.stop_reason}")
            break
    
    # 최대 반복 도달
    print("⚠️ Agent 최대 반복 도달")
    
    answer = ""
    for content in response.content:
        if content.type == "text":
            answer += content.text
    
    return {
        "message": answer or "죄송합니다. 답변을 생성하지 못했습니다.",
        **accumulated_results
    }


def chat_with_claude(
    message: str,
    db: Session,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None
) -> Dict[str, Any]:
    """Claude Agent - Sync 래퍼"""
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            chat_with_claude_async(message, db, user_latitude, user_longitude)
        )
        return result
    finally:
        loop.close()