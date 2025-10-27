"""
Claude + MCP 기반 자율 AI Agent
"""
import os
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from anthropic import Anthropic

from . import schemas
from .mcp_client import mcp_client

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
    {
        "name": "get_today_meals",
        "description": "오늘의 학식 메뉴를 조회합니다",
        "input_schema": {"type": "object", "properties": {
            "cafeteria": {"type": "string", "enum": ["student", "faculty", "dormitory"]}
        }}
    },
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
    }
]


async def process_tool_call_async(
    tool_name: str,
    tool_input: Dict,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None
) -> Dict[str, Any]:
    """MCP Tool 실행"""
    
    try:
        if tool_name == "search_classroom":
            query = tool_input.get("query", "")
            
            result = await mcp_client.call_tool(
                "classroom",
                "search_classroom",
                {"query": query}
            )
            
            classrooms = json.loads(result) if isinstance(result, str) else result
            
            if classrooms and len(classrooms) > 0:
                classroom = classrooms[0]
                
                from .utils import generate_naver_map_link
                classroom_obj = schemas.ClassroomInfo(**classroom)
                map_link = generate_naver_map_link(
                    classroom_obj,
                    user_latitude,
                    user_longitude
                )
                
                return {
                    "found": True,
                    "classroom": classroom,
                    "map_link": map_link
                }
            else:
                return {
                    "found": False,
                    "message": "강의실을 찾을 수 없습니다"
                }
        
        elif tool_name == "search_notices":
            query = tool_input.get("query", "")
            limit = tool_input.get("limit", 5)
            
            result = await mcp_client.call_tool(
                "notice",
                "search_notices",
                {"query": query, "limit": limit}
            )
            
            notices = json.loads(result) if isinstance(result, str) else result
            
            return {
                "found": len(notices) > 0,
                "notices": notices
            }
        
        elif tool_name == "get_latest_notices":
            source = tool_input.get("source", "swedu")
            limit = tool_input.get("limit", 5)
            
            result = await mcp_client.call_tool(
                "notice",
                "get_latest_notices",
                {"source": source, "limit": limit}
            )
            
            notices = json.loads(result) if isinstance(result, str) else result
            
            return {
                "found": len(notices) > 0,
                "notices": notices
            }
        
        elif tool_name == "crawl_fresh_notices":
            source = tool_input.get("source", "swedu")
            limit = tool_input.get("limit", 20)
            
            result = await mcp_client.call_tool(
                "notice",
                "crawl_fresh_notices",
                {"source": source, "limit": limit}
            )
            
            return {
                "found": True,
                "message": result if isinstance(result, str) else "크롤링 완료"
            }
        
        elif tool_name == "search_courses":
            department = tool_input.get("department", "소프트웨어융합학과")
            keyword = tool_input.get("keyword", "")
            
            result = await mcp_client.call_tool(
                "course",
                "search_courses", 
                {"department": department, "keyword": keyword}
            )
            
            courses = json.loads(result) if isinstance(result, str) else result
            
            return {
                "found": len(courses.get("courses", [])) > 0 if isinstance(courses, dict) else False,
                "courses": courses
            }
        
        elif tool_name == "search_curriculum":
            query = tool_input.get("query", "")
            year = tool_input.get("year", "latest")
            
            result = await mcp_client.call_tool(
                "curriculum",
                "search_courses",
                {"query": query, "year": year}
            )
            
            curriculum_data = json.loads(result) if isinstance(result, str) else result
            
            return {
                "found": curriculum_data.get("found", False),
                "count": curriculum_data.get("count", 0),
                "year": curriculum_data.get("year", year),
                "courses": curriculum_data.get("courses", [])
            }
        
        elif tool_name == "get_curriculum_by_semester":
            semester = tool_input.get("semester")
            year = tool_input.get("year", "latest")
            
            result = await mcp_client.call_tool(
                "curriculum",
                "get_courses_by_semester",
                {"semester": semester, "year": year}
            )
            
            curriculum_data = json.loads(result) if isinstance(result, str) else result
            
            return {
                "found": curriculum_data.get("found", False),
                "semester": semester,
                "year": curriculum_data.get("year", year),
                "count": curriculum_data.get("count", 0),
                "courses": curriculum_data.get("courses", [])
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
    db: Session,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None
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
    
    system_prompt = """당신은 경희대학교 소프트웨어융합대학의 자율 AI Agent입니다.

당신의 역할:
1. 사용자 질문을 분석하고 필요한 정보를 파악합니다
2. 여러 도구를 조합하여 복잡한 질문에 답변합니다
3. 부족한 정보가 있으면 추가 도구를 사용합니다
4. 모든 정보를 종합하여 완전한 답변을 제공합니다

사용 가능한 MCP Tools:
- search_classroom: 강의실/연구실/편의시설 검색
- search_notices: 공지사항 키워드 검색
- get_latest_notices: 최신 공지사항 조회
- crawl_fresh_notices: 실시간 공지 크롤링
- search_curriculum: 교과과정 과목 검색 (과목명, 학점, 선수과목 정보 제공)
- get_curriculum_by_semester: 학기별 개설 과목 조회

Agent 행동 원칙:
- 복잡한 질문은 여러 도구로 나누어 해결
- 각 도구의 결과를 확인하고 다음 행동 결정
- 필요시 추가 도구 호출
- 모든 정보를 종합하여 완전한 답변 제공

답변 스타일:
- 친근하고 간결하게
- Markdown 사용 금지
- 이모지 적절히 사용"""

    messages = [{"role": "user", "content": message}]
    
    # Agent Loop: 최대 5번 반복 (무한 루프 방지)
    max_iterations = 5
    iteration = 0
    
    accumulated_results = {
        "classrooms": [],
        "notices": [],
        "map_links": [],
        "courses": [],  # 수강신청 과목 (course-mcp)
        "curriculum_courses": []  # 교과과정 과목 (curriculum-mcp)
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
                        user_longitude
                    )
                    
                    # 결과 누적
                    if "classroom" in result:
                        accumulated_results["classrooms"].append(result["classroom"])
                        if "map_link" in result:
                            accumulated_results["map_links"].append(result["map_link"])
                    
                    if "notices" in result:
                        accumulated_results["notices"].extend(result["notices"])
                    
                    # curriculum 결과 처리 (search_curriculum, get_curriculum_by_semester)
                    if content.name in ["search_curriculum", "get_curriculum_by_semester"]:
                        if "courses" in result and isinstance(result["courses"], list):
                            accumulated_results["curriculum_courses"].extend(result["courses"])
                    # course 결과 처리 (search_courses)
                    elif "courses" in result and isinstance(result["courses"], list):
                        accumulated_results["courses"].extend(result["courses"])
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
            
            # 대화 이력 업데이트
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # 다음 반복으로 (Agent가 추가 Tool 사용 판단)
            
        elif response.stop_reason == "end_turn":
            # Agent가 더 이상 Tool 사용 안함 → 최종 답변 생성
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
            
            return result
        
        else:
            # 기타 종료 이유
            print(f"⚠️ Agent 종료: {response.stop_reason}")
            break
    
    # 최대 반복 도달
    print("⚠️ Agent 최대 반복 도달")
    
    # 마지막 응답이라도 반환
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