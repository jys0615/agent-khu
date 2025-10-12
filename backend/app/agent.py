from openai import OpenAI
from sqlalchemy.orm import Session
from . import crud, schemas
from typing import Optional, Tuple, List
import os
import json
import re
import subprocess

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Python 스크립트 경로
SCRAPER_PATH = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/khu-notice-mcp/scrapers/khu_scraper.py")


def run_scraper(source: str, limit: int = 20) -> List[dict]:
    """Python 크롤러 스크립트 직접 실행"""
    try:
        result = subprocess.run(
            ["/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
             SCRAPER_PATH, source, str(limit)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return []
        
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Scraper error: {e}")
        return []


def extract_classroom_code(text: str) -> Optional[str]:
    """텍스트에서 강의실 코드 추출"""
    pattern1 = r'전\s*(\d+)'
    match1 = re.search(pattern1, text)
    if match1:
        return f"전{match1.group(1)}"
    
    pattern2 = r'전자정보대학관\s*(\d+)\s*호'
    match2 = re.search(pattern2, text)
    if match2:
        return f"전{match2.group(1)}"
    
    return None


def generate_naver_map_link(
    classroom: schemas.Classroom,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None
) -> str:
    """네이버 지도 웹 URL 생성"""
    dest_lat = classroom.latitude or 37.2420
    dest_lon = classroom.longitude or 127.0794
    
    destination_name = f"{classroom.building_name} {classroom.room_number}호"
    
    if user_lat and user_lon:
        return f"https://map.naver.com/p/directions/{user_lon},{user_lat},{dest_lon},{dest_lat},walk/"
    else:
        return f"https://map.naver.com/p/search/{destination_name}?c={dest_lon},{dest_lat},18,0,0,0,dh"


def get_classroom_info_function():
    """강의실/공간 정보 조회 Function"""
    return {
        "type": "function",
        "function": {
            "name": "get_classroom_info",
            "description": """경희대학교 전자정보대학관의 강의실, 연구실, 행정실 등 공간 정보를 조회합니다.
            
검색 가능한 정보:
- 강의실 번호 (예: 101, 전101, B08)
- 교수님 이름 (예: 조진성, 홍충선)
- 공간 유형 (예: 학생회실, 매점, 세미나실)
- 키워드 (예: 화장실, 휴게실)""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 내용 (강의실 번호, 교수님 이름, 공간명 등)"
                    }
                },
                "required": ["query"]
            }
        }
    }


def get_notice_search_function():
    """공지사항 검색 Function"""
    return {
        "type": "function",
        "function": {
            "name": "search_notices",
            "description": "경희대 소프트웨어융합대학 공지사항을 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 키워드"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "결과 개수 (기본값: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }


def get_latest_notices_function():
    """최신 공지사항 조회 Function"""
    return {
        "type": "function",
        "function": {
            "name": "get_latest_notices",
            "description": "경희대 소프트웨어융합대학 최신 공지사항을 가져옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "소스 (swedu: SW사업단, department: 학과, schedule: 학사일정)",
                        "enum": ["swedu", "department", "schedule"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "가져올 공지 개수 (기본값: 5)",
                        "default": 5
                    }
                }
            }
        }
    }


async def chat_with_agent(
    db: Session,
    user_message: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None
) -> Tuple[str, Optional[schemas.Classroom], Optional[str], bool, Optional[List[schemas.Notice]], bool]:
    """OpenAI Agent와 대화"""
    
    system_prompt = """당신은 경희대학교 소프트웨어융합대학 학생들을 위한 AI 어시스턴트입니다.

주요 역할:
1. 전자정보대학관 공간 안내
   - 강의실 (101, 102, 전101 등)
   - 교수님 연구실 (교수님 이름으로 검색 가능)
   - 학생회실, 세미나실, 매점, 화장실 등
   - 총 314개 공간 정보 보유

2. 학과 및 SW사업단 공지사항 안내
   - SW중심대학사업단 공지
   - 컴퓨터공학부 공지
   - 학사일정

검색 예시:
- "전101 어디야?" → 강의실 정보
- "조진성 교수님 연구실 어디?" → 301호
- "학생회실 어디야?" → 240호 (소프트웨어융합대학/컴퓨터공학부학생회실)
- "매점 어디?" → 112호 (휴게실/매점)
- "화장실 어디?" → 가장 가까운 화장실 안내
- "세미나실 있어?" → 세미나실 목록

답변 스타일:
- 친근하고 간결하게
- 정보를 명확히 전달
- 추가 도움이 필요한지 물어보기
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=[
            get_classroom_info_function(),
            get_notice_search_function(),
            get_latest_notices_function()
        ],
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    classroom_info = None
    map_link = None
    show_map_button = False
    notices = None
    show_notices = False
    
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # 강의실/공간 정보 조회
            if function_name == "get_classroom_info":
                query = function_args.get("query")
                
                # 먼저 정확한 코드로 검색
                classroom = crud.get_classroom_by_code(db, query)
                
                # 없으면 키워드 검색
                if not classroom:
                    classrooms = crud.search_classrooms(db, query, 1)
                    if classrooms:
                        classroom = classrooms[0]
                
                if classroom:
                    classroom_info = schemas.Classroom.model_validate(classroom)
                    map_link = generate_naver_map_link(classroom_info, user_lat, user_lon)
                    show_map_button = True
                    
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    })
                    
                    # 공간 유형별 설명 추가
                    room_type_desc = {
                        'classroom': '강의실',
                        'professor_office': '교수 연구실',
                        'lab': '연구실/실험실',
                        'admin_office': '행정실',
                        'student_council': '학생회실',
                        'seminar_room': '세미나실',
                        'amenity': '편의시설',
                        'restroom': '화장실',
                        'club_room': '동아리방',
                        'other': '기타'
                    }
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({
                            "code": classroom.code,
                            "name": classroom.room_name,
                            "type": room_type_desc.get(classroom.room_type, classroom.room_type),
                            "floor": f"지하 {classroom.floor[1:]}층" if classroom.floor == 'B' else f"{classroom.floor}층",
                            "professor": classroom.professor_name if classroom.professor_name else None,
                            "accessible": "학생 접근 가능" if classroom.is_accessible else "제한 구역"
                        }, ensure_ascii=False)
                    })
            
            # 공지사항 검색 (기존 로직 유지)
            elif function_name == "search_notices":
                query = function_args.get("query")
                limit = function_args.get("limit", 5)
                
                db_notices = crud.search_notices(db, query, limit)
                
                if not db_notices:
                    posts = run_scraper("swedu", 20)
                    for post in posts:
                        crud.create_notice_from_mcp(db, post)
                    db_notices = crud.search_notices(db, query, limit)
                
                if db_notices:
                    notices = [schemas.Notice.model_validate(n) for n in db_notices]
                    show_notices = True
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps([{
                        "title": n.title,
                        "source": n.source,
                        "date": n.date
                    } for n in db_notices], ensure_ascii=False)
                })
            
            # 최신 공지사항 조회 (기존 로직 유지)
            elif function_name == "get_latest_notices":
                source = function_args.get("source", "swedu")
                limit = function_args.get("limit", 5)
                
                db_notices = crud.get_latest_notices(db, source=source, limit=limit)
                
                if not db_notices:
                    posts = run_scraper(source, limit)
                    for post in posts:
                        crud.create_notice_from_mcp(db, post)
                    db_notices = crud.get_latest_notices(db, source=source, limit=limit)
                
                if db_notices:
                    notices = [schemas.Notice.model_validate(n) for n in db_notices]
                    show_notices = True
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps([{
                        "title": n.title,
                        "source": n.source,
                        "date": n.date
                    } for n in db_notices], ensure_ascii=False)
                })
        
        # 최종 응답 생성
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        ai_message = final_response.choices[0].message.content
    else:
        ai_message = response_message.content
    
    return ai_message, classroom_info, map_link, show_map_button, notices, show_notices