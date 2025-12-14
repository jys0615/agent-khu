"""
Agent 메인 루프
"""
import os
import json
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from anthropic import Anthropic
from .. import models
from ..observability import obs_logger
from ..question_classifier import classifier
from .tools_definition import tools
from .tool_executor import process_tool_call
from .utils import detect_curriculum_intent, build_system_prompt

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


async def chat_with_claude_async(
    message: str,
    db: Session,
    user_latitude: Optional[float] = None,
    user_longitude: Optional[float] = None,
    library_username: Optional[str] = None,
    library_password: Optional[str] = None,
    current_user: Optional[models.User] = None
) -> Dict[str, Any]:
    """
    Claude 기반 자율 Agent (with Observability)
    """
    # Observability 시작
    start_time = time.time()
    question_type = classifier.classify(message)
    mcp_tools_used = []
    
    print(f"📊 Question Type: {question_type.upper()}")
    print(f"📝 Classification: {classifier.get_classification_reason(message)}")
    
    try:
        # System prompt 생성
        hint = detect_curriculum_intent(message)
        hint_text = ""
        if hint.get("intent"):
            hint_text = f"\n[HINT] curriculum_intent={hint['intent']}\n"
        
        system_prompt = build_system_prompt(current_user, hint_text)
        
        messages = [{"role": "user", "content": message}]
        
        # Agent Loop
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
                
                for content in response.content:
                    if content.type == "tool_use":
                        print(f"  🔧 Tool 사용: {content.name}")
                        mcp_tools_used.append(content.name)
                        
                        # Tool 실행
                        result = await process_tool_call(
                            content.name,
                            content.input,
                            user_latitude,
                            user_longitude,
                            library_username,
                            library_password,
                            current_user
                        )
                        
                        # 결과 누적
                        _accumulate_results(accumulated_results, content.name, result)
                        
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
                result = _build_final_result(answer, accumulated_results)
                
                # Observability 로깅
                await obs_logger.log_interaction(
                    question=message,
                    user_id=current_user.student_id if current_user else "anonymous",
                    question_type=question_type,
                    routing_decision="llm",
                    mcp_tools_used=mcp_tools_used,
                    response=result["message"],
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=True
                )
                
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
        
        result = {
            "message": answer or "죄송합니다. 답변을 생성하지 못했습니다.",
            **accumulated_results
        }
        
        # Observability 로깅
        await obs_logger.log_interaction(
            question=message,
            user_id=current_user.student_id if current_user else "anonymous",
            question_type=question_type,
            routing_decision="llm",
            mcp_tools_used=mcp_tools_used,
            response=result["message"],
            latency_ms=int((time.time() - start_time) * 1000),
            success=True
        )
        
        return result
    
    except Exception as e:
        print(f"❌ Agent 에러: {e}")
        
        # 에러 로깅
        await obs_logger.log_interaction(
            question=message,
            user_id=current_user.student_id if current_user else "anonymous",
            question_type=question_type,
            routing_decision="llm",
            mcp_tools_used=mcp_tools_used,
            response=str(e),
            latency_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=str(e)
        )
        raise


def _accumulate_results(accumulated_results: dict, tool_name: str, result: dict):
    """Tool 실행 결과 누적"""
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
    
    if tool_name in ["search_curriculum", "get_curriculum_by_semester"]:
        if "courses" in result and isinstance(result["courses"], list):
            accumulated_results["curriculum_courses"].extend(result["courses"])
    elif "courses" in result and isinstance(result["courses"], list):
        accumulated_results["courses"].extend(result["courses"])
    
    if tool_name == "get_requirements" and result.get("found"):
        accumulated_results["requirements_result"] = result["requirements"]
    
    if tool_name == "evaluate_progress" and result.get("found"):
        accumulated_results["progress_result"] = result["evaluation"]
    
    if tool_name == "get_library_info" and "library_info" in result:
        accumulated_results["library_info"] = result["library_info"]
    
    if tool_name == "get_seat_availability" and "library_seats" in result:
        accumulated_results["library_seats"] = result["library_seats"]
    
    if tool_name == "reserve_seat" and "reservation" in result:
        accumulated_results["reservation"] = result["reservation"]


def _build_final_result(answer: str, accumulated_results: dict) -> dict:
    """최종 결과 구성"""
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
    
    # 도서관 결과 처리
    if accumulated_results["library_seats"]:
        result["library_seats"] = accumulated_results["library_seats"]
        result["show_library_seats"] = True
    elif accumulated_results["library_info"]:
        result["library_info"] = accumulated_results["library_info"]
        result["show_library_info"] = True
    
    if accumulated_results["reservation"]:
        result["reservation"] = accumulated_results["reservation"]
        result["show_reservation"] = True
    
    if accumulated_results["needs_library_login"]:
        result["needs_library_login"] = True
    
    return result


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
