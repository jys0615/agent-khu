from openai import OpenAI
from sqlalchemy.orm import Session
from . import crud, schemas
from .mcp_client import instagram_mcp_client
from typing import Optional, Tuple, List
import os
import json
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_classroom_code(text: str) -> Optional[str]:
    """
    텍스트에서 강의실 코드 추출
    """
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
    """
    네이버 지도 웹 URL 생성
    """
    dest_lat = classroom.latitude or 37.2420
    dest_lon = classroom.longitude or 127.0794
    
    destination_name = f"{classroom.building_name} {classroom.room_number}호"
    
    if user_lat and user_lon:
        # 길찾기 URL
        return f"https://map.naver.com/p/directions/{user_lon},{user_lat},{dest_lon},{dest_lat},walk/"
    else:
        # 장소 검색 URL
        return f"https://map.naver.com/p/search/{destination_name}?c={dest_lon},{dest_lat},18,0,0,0,dh"


def get_classroom_info_function():
    """
    강의실 정보 조회 Function
    """
    return {
        "type": "function",
        "function": {
            "name": "get_classroom_info",
            "description": "경희대학교 강의실 정보를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "classroom_code": {
                        "type": "string",
                        "description": "강의실 코드 (예: 전101, 전202)"
                    }
                },
                "required": ["classroom_code"]
            }
        }
    }


def get_notice_search_function():
    """
    공지사항 검색 Function
    """
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
    """
    최신 공지사항 조회 Function
    """
    return {
        "type": "function",
        "function": {
            "name": "get_latest_notices",
            "description": "경희대 소프트웨어융합대학 최신 공지사항을 가져옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "가져올 공지 개수 (기본값: 5)",
                        "default": 5
                    }
                },
            }
        }
    }


async def chat_with_agent(
    db: Session,
    user_message: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None
) -> Tuple[str, Optional[schemas.Classroom], Optional[str], bool, Optional[List[schemas.Notice]], bool]:
    """
    OpenAI Agent와 대화
    
    Returns:
        (응답 메시지, 강의실 정보, 지도 링크, 지도 버튼 표시, 공지사항 목록, 공지사항 표시)
    """
    
    system_prompt = """당신은 경희대학교 소프트웨어융합대학 학생들을 위한 AI 어시스턴트입니다.

주요 역할:
1. 강의실 위치 안내
2. 학생회 공지사항 안내
3. 학사 정보 제공

답변 스타일:
- 친근하고 간결하게
- 정보를 명확히 전달
- 추가 도움이 필요한지 물어보기

예시:
- 사용자: "최근 공지 알려줘"
- AI: "최근 소프트웨어융합대학 학생회 공지사항을 확인해드릴게요!"
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Function Calling with all functions
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
    
    # Function Call 처리
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # 강의실 정보 조회
            if function_name == "get_classroom_info":
                classroom_code = function_args.get("classroom_code")
                classroom = crud.get_classroom_by_code(db, classroom_code)
                
                if classroom:
                    classroom_info = schemas.Classroom.from_orm(classroom)
                    map_link = generate_naver_map_link(classroom_info, user_lat, user_lon)
                    show_map_button = True
                    
                    messages.append(response_message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({
                            "code": classroom.code,
                            "building": classroom.building_name,
                            "room": classroom.room_number,
                            "floor": classroom.floor
                        }, ensure_ascii=False)
                    })
            
            # 공지사항 검색
            elif function_name == "search_notices":
                query = function_args.get("query")
                limit = function_args.get("limit", 5)
                
                # MCP Server 통해 검색
                posts = await instagram_mcp_client.search_posts(query, limit)
                
                # DB에 저장 및 조회
                for post in posts:
                    crud.create_notice_from_instagram(db, post)
                
                db_notices = crud.search_notices(db, query, limit)
                if db_notices:
                    notices = [schemas.Notice.from_orm(n) for n in db_notices]
                    show_notices = True
                
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps([{
                        "title": n.title,
                        "posted_at": n.posted_at.isoformat()
                    } for n in db_notices], ensure_ascii=False)
                })
            
            # 최신 공지사항 조회
            elif function_name == "get_latest_notices":
                limit = function_args.get("limit", 5)
                
                # MCP Server 통해 최신 게시물 가져오기
                posts = await instagram_mcp_client.get_posts(limit)
                
                # DB에 저장
                for post in posts:
                    crud.create_notice_from_instagram(db, post)
                
                db_notices = crud.get_latest_notices(db, limit)
                if db_notices:
                    notices = [schemas.Notice.from_orm(n) for n in db_notices]
                    show_notices = True
                
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps([{
                        "title": n.title,
                        "posted_at": n.posted_at.isoformat()
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