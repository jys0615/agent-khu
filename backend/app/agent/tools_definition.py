"""
MCP Tools 정의
"""

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
        "description": "학과 공지사항을 키워드로 검색합니다 (전체 학과 통합 검색)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 키워드"},
                "limit": {"type": "integer", "default": 5, "description": "결과 개수"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_latest_notices",
        "description": "학과별 최신 공지사항 조회. 사용자가 특정 학과의 공지사항을 물어보면 이 tool을 사용합니다. 지원 학과: 소프트웨어융합학과, 컴퓨터공학부, 전자공학과, 산업경영공학과. 학과를 명시하지 않으면 사용자 학과를 사용합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "학과명. 사용자가 학과를 명시하지 않으면 비워둡니다.",
                    "enum": ["소프트웨어융합학과", "컴퓨터공학부", "전자공학과", "산업경영공학과"]
                },
                "limit": {"type": "integer", "default": 5, "description": "결과 개수"}
            }
        }
    },
    {
        "name": "crawl_fresh_notices",
        "description": "실시간으로 공지사항을 크롤링합니다 (최신 정보 필요 시)",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "enum": ["소프트웨어융합학과", "컴퓨터공학부", "전자공학과", "산업경영공학과"]
                },
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "search_meals",
        "description": "특정 메뉴가 나오는 날을 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색할 메뉴"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_next_shuttle",
        "description": "다음 셔틀버스 시간을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "route": {"type": "string", "enum": ["to_station", "to_campus"]}
            }
        }
    },
    {
        "name": "search_courses",
        "description": "학과별 개설 교과목을 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "학과명 (예: 소프트웨어융합학과)"},
                "keyword": {"type": "string", "description": "검색 키워드 (과목명, 교수명)"}
            }
        }
    },
    {
        "name": "search_curriculum",
        "description": "소프트웨어융합대학 교과과정에서 과목을 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색할 과목명 또는 과목코드"},
                "year": {"type": "string", "description": "학년도", "default": "latest"}
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
                "semester": {"type": "string", "enum": ["1학기", "2학기"]},
                "year": {"type": "string", "default": "latest"}
            },
            "required": ["semester"]
        }
    },
    {
        "name": "list_programs",
        "description": "해당 연도의 전공 코드 목록을 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "string", "default": "latest"}
            }
        }
    },
    {
        "name": "get_requirements",
        "description": "졸업요건 조회. 로그인한 사용자의 경우 program과 year를 생략하면 자동으로 채워집니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {
                    "type": "string", 
                    "description": "전공 코드 (예: KHU-CSE). 생략 가능 (로그인 시 자동)"
                },
                "year": {
                    "type": "string", 
                    "description": "입학년도 (예: 2019). 생략 가능 (로그인 시 자동)"
                }
            },
            "required": []  # ✅ 필수 아님!
        }
    },
    {
        "name": "evaluate_progress",
        "description": "졸업요건 충족도 평가. program, year 생략 가능 (로그인 시 자동)",
        "input_schema": {
            "type": "object",
            "properties": {
                "program": {"type": "string", "description": "전공 코드. 생략 가능"},
                "year": {"type": "string", "description": "입학년도. 생략 가능"},
                "taken_courses": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["taken_courses"] 
        }
    },
    {
        "name": "get_library_info",
        "description": "경희대 도서관 기본 정보 조회 (운영시간, 위치 등)",
        "input_schema": {
            "type": "object",
            "properties": {
                "campus": {"type": "string", "enum": ["seoul", "global"], "default": "global"}
            }
        }
    },
    {
        "name": "get_seat_availability",
        "description": "경희대 도서관 실시간 좌석 현황 조회 (로그인 필요). 사용자가 도서관 좌석 정보를 물어볼 때 사용합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campus": {"type": "string", "enum": ["seoul", "global"], "default": "global"}
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
                "seat_number": {"type": "string", "description": "좌석 번호 (선택)"}
            },
            "required": ["room"]
        }
    },
    {
        "name": "get_today_meal",
        "description": "오늘의 학식 메뉴를 조회합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal_type": {"type": "string", "enum": ["lunch", "dinner"], "default": "lunch"}
            }
        }
    },
    {
        "name": "get_cafeteria_info",
        "description": "학생회관 식당 기본 정보를 조회합니다",
        "input_schema": {"type": "object", "properties": {}}
    }
]

# 캐시 TTL 설정 (초 단위)
CACHE_TTL = {
    "search_classroom": 86400,
    "search_notices": 7200,      # 2시간 (1시간 → 2시간)
    "get_latest_notices": 7200,
    "search_curriculum": 86400,
    "get_requirements": 86400,   # ✅ 추가
    "evaluate_progress": 3600,   # ✅ 추가 (1시간)
    "get_library_info": 3600,    # 5분 → 1시간
    "get_seat_availability": 60,
    "get_next_shuttle": 300,     # 3분 → 5분
    "get_cafeteria_info": 86400,
    "get_today_meal": 3600,      # ✅ 추가 (1시간)
}