"""
Agent 메인 루프
"""
import os
import json
import time
import asyncio  # ✅ 추가
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from anthropic import Anthropic
from .. import models
from ..observability import obs_logger
from ..question_classifier import classifier
from .tools_definition import tools
from .tool_executor import process_tool_call
from .utils import detect_curriculum_intent, build_system_prompt

# SLM Agent 조건부 import
try:
    from ..slm_agent import get_slm_agent
    SLM_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️ SLM Agent 사용 불가 (torch 미설치): {e}")
    SLM_AVAILABLE = False
    def get_slm_agent():
        class DummySLM:
            enabled = False
        return DummySLM()

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
    Hybrid Agent: Simple → SLM, Complex → LLM (with Observability)
    """
    # Observability 시작
    start_time = time.time()
    question_type = classifier.classify(message)
    mcp_tools_used = []
    routing_decision = "llm"  # 기본값
    
    print(f"📊 Question Type: {question_type.upper()}")
    print(f"📝 Classification: {classifier.get_classification_reason(message)}")
    
    # 🆕 Simple 질문 → SLM 시도
    if question_type == "simple":
        slm = get_slm_agent()
        if slm.enabled:
            print("🟢 SLM으로 처리 시도...")
            slm_result = await slm.generate(message)
            
            if slm_result["success"] and slm_result["confidence"] >= 0.7:
                print(f"✅ SLM 성공 (confidence: {slm_result['confidence']:.2f})")
                routing_decision = "slm"
                
                # Observability 로깅
                await obs_logger.log_interaction(
                    question=message,
                    user_id=current_user.student_id if current_user else "anonymous",
                    question_type=question_type,
                    routing_decision=routing_decision,
                    mcp_tools_used=[],
                    response=slm_result["message"],
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=True
                )
                
                return {"message": slm_result["message"]}
            else:
                print(f"⚠️ SLM 품질 낮음 (confidence: {slm_result.get('confidence', 0):.2f}), LLM Fallback")
                routing_decision = "llm_fallback"
    
    # 🔵 Complex 질문 또는 SLM 실패 → LLM 사용
    print(f"🔵 LLM (Claude)으로 처리... (routing: {routing_decision})")
    
    try:
        # System prompt 생성
        hint = detect_curriculum_intent(message)
        hint_text = ""
        if hint.get("intent"):
            hint_text = f"\n[HINT] curriculum_intent={hint['intent']}\n"
        if hint.get("year"):
            hint_text += f"[HINT] requested_year={hint['year']}\n"
        
        system_prompt = build_system_prompt(current_user, hint_text)
        
        # 🔍 디버깅: 사용자 정보 및 시스템 프롬프트 확인
        if current_user:
            print(f"✅ 로그인 사용자:")
            print(f"   └─ 학번: {current_user.student_id}")
            print(f"   └─ 입학년도: {current_user.admission_year}년")
            print(f"   └─ 학과: {current_user.department}")
            print(f"   └─ 캠퍼스: {current_user.campus}")
            print(f"   └─ 이수학점: {current_user.completed_credits or 0}/130")
            print(f"   └─ [자동 적용] get_requirements, evaluate_progress 툴에서 사용됨")
        else:
            print(f"⚠️  미로그인 상태 (current_user is None)")
            print(f"   └─ 수동으로 program/year를 명시해야 함")
        print(f"🔍 DEBUG - System Prompt 길이: {len(system_prompt)} chars")
        print(f"🔍 DEBUG - System Prompt 앞부분:\n{system_prompt[:500]}...")
        
        messages = [{"role": "user", "content": message}]
        
        # Agent Loop
        max_iterations = 2
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
            "meal_result": None,
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
            # Tool 사용 여부 확인
            if response.stop_reason == "tool_use":
                tool_results = []
                
                print(f"🔍 DEBUG - Claude가 tool을 호출했습니다!")
                
                # Tool 호출 목록 수집
                tool_calls = []
                for content in response.content:
                    if content.type == "tool_use":
                        print(f"  🔧 Tool 사용: {content.name}")
                        print(f"  🔧 Tool 파라미터: {content.input}")
                        mcp_tools_used.append(content.name)
                        tool_calls.append(content)
                
                # 🚀 순차 실행 (MCP stdio 안정성을 위해)
                print(f"⚡ {len(tool_calls)}개 Tool 순차 실행 시작...")
                results = []
                for tool in tool_calls:
                    result = await process_tool_call(
                        tool.name,
                        tool.input,
                        user_latitude,
                        user_longitude,
                        library_username,
                        library_password,
                        current_user
                    )
                    results.append(result)
                    await asyncio.sleep(0.1)  # 짧은 대기 시간
                
                # 결과 처리
                for tool, result in zip(tool_calls, results):
                    # 결과 누적
                    _accumulate_results(accumulated_results, tool.name, result)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                
                print(f"✅ 순차 실행 완료")
                
                # 대화 이력 업데이트
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            
            elif response.stop_reason == "end_turn":
                print("✅ Agent 작업 완료")
                print(f"🔍 DEBUG - stop_reason: end_turn (tool 호출 안함)")
                
                # 최종 응답 추출
                answer = ""
                for content in response.content:
                    if content.type == "text":
                        answer += content.text
                        print(f"🔍 DEBUG - Claude 답변: {answer[:200]}...")
                
                # 결과 구성
                result = _build_final_result(answer, accumulated_results)
                
                # Observability 로깅
                await obs_logger.log_interaction(
                    question=message,
                    user_id=current_user.student_id if current_user else "anonymous",
                    question_type=question_type,
                    routing_decision=routing_decision,
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
            routing_decision=routing_decision,
            mcp_tools_used=mcp_tools_used,
            response=result["message"],
            latency_ms=int((time.time() - start_time) * 1000),
            success=True
        )
        
        return result
    
    except Exception as e:
        print(f"❌ Agent 에러: {e}")
        
        # ▼ Fallback: LLM 불가 시 직접 MCP 도구를 호출하여 응답 생성
        try:
            fb = await _fallback_direct_response(
                message=message,
                current_user=current_user,
                question_type=question_type,
                mcp_tools_used=mcp_tools_used,
            )
            if fb:
                # Observability 로깅 (성공으로 기록, 라우팅은 fallback)
                await obs_logger.log_interaction(
                    question=message,
                    user_id=current_user.student_id if current_user else "anonymous",
                    question_type=question_type,
                    routing_decision="fallback_direct",
                    mcp_tools_used=fb.get("_mcp_tools_used", []),
                    response=fb["message"],
                    latency_ms=int((time.time() - start_time) * 1000),
                    success=True
                )
                fb.pop("_mcp_tools_used", None)
                return fb
        except Exception as fe:
            print(f"⚠️ Fallback 실패: {fe}")

        # 에러 로깅 (최종)
        await obs_logger.log_interaction(
            question=message,
            user_id=current_user.student_id if current_user else "anonymous",
            question_type=question_type,
            routing_decision=routing_decision,
            mcp_tools_used=mcp_tools_used,
            response=str(e),
            latency_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=str(e)
        )
        # 사용자에게는 간단한 오류 메시지 반환
        return {"message": "죄송합니다. 현재 LLM 연결이 원활하지 않습니다. 잠시 후 다시 시도해주세요."}


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
    
    # ✅ list_programs 결과 처리 추가
    if tool_name == "list_programs" and result.get("found"):
        programs_data = result.get("programs", [])
        # programs를 정리된 형식으로 변환
        formatted_programs = []
        for prog in programs_data:
            formatted_programs.append({
                "code": prog.get("code"),
                "name": prog.get("name"),
                "credits": prog.get("total_credits")
            })
        # Claude의 다음 턴에서 참고할 수 있도록 저장 (현재는 결과로 반환하지 않음)
        # 이는 Claude에게 list_programs 호출 후 get_requirements 호출을 유도하기 위함
    
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

    # 🧑‍🍳 학식 결과 누적
    if tool_name == "get_today_meal" and "meals" in result:
        accumulated_results["meal_result"] = result["meals"]


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
        # 📌 메시지에 졸업요건 요약 추가 (사용자 입학년도 반영 결과가 보이도록)
        try:
            req = accumulated_results["requirements_result"]
            year = req.get("year")
            prog = req.get("program_name") or req.get("program")
            total = req.get("total_credits")
            major = req.get("major_credits")

            # 그룹 요약 (최대 4개)
            groups = req.get("groups") or []
            group_lines = []
            for g in groups[:4]:
                name = g.get("name")
                mc = g.get("min_credits")
                if name and mc is not None:
                    group_lines.append(f"- {name}: {mc}학점")

            summary_lines = [
                f"\n## 📋 {year}학번 {prog} 졸업요건 요약",
                f"- 총 이수학점: {total}학점",
                f"- 전공 이수학점: {major}학점",
            ]
            if group_lines:
                summary_lines.append("- 전공 이수 구분:")
                summary_lines.extend(group_lines)

            # 기존 메시지 뒤에 추가 (중복 방지 최소화는 생략: 최신 데이터가 더 정확)
            result["message"] = (result["message"] or "").rstrip() + "\n" + "\n".join(summary_lines)
        except Exception:
            pass
    
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

    # 🧑‍🍳 학식 결과 구성: 메시지에 출처 링크 포함
    if accumulated_results["meal_result"]:
        meal = accumulated_results["meal_result"]
        result["meals"] = meal
        result["show_meals"] = True
        # 답변 텍스트에 원본 링크가 없으면 추가
        try:
            src = meal.get("source_url") or meal.get("menu_url")
            if src:
                # 중복 추가 방지
                if src not in result["message"]:
                    result["message"] = (
                        result["message"].rstrip() + f"\n원본 메뉴표: {src}"
                    )
        except Exception:
            pass
    
    return result


async def _fallback_direct_response(
    message: str,
    current_user: Optional[models.User],
    question_type: str,
    mcp_tools_used: list,
) -> Optional[Dict[str, Any]]:
    """LLM 호출 실패 시 최소한의 규칙 기반으로 MCP 도구를 직접 호출하여 응답을 구성.
    현재는 졸업요건 질의(requirements)에 대해 `get_requirements`만 처리한다.
    """
    hint = detect_curriculum_intent(message)
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
        "meal_result": None,
    }

    tools_used = []

    # 졸업요건 의도면 get_requirements 직접 호출
    if (hint.get("intent") == "requirements") or ("졸업" in message and "요건" in message):
        res = await process_tool_call("get_requirements", {}, current_user=current_user)
        tools_used.append("get_requirements")

        # 성공 시 즉시 구조화 응답 반환
        if res and res.get("found") and isinstance(res.get("requirements"), dict):
            req = res["requirements"]
            try:
                year = req.get("year")
                prog = req.get("program_name") or req.get("program")
                total = req.get("total_credits")
                major = req.get("major_credits")
                msg = f"## 📋 {year}학번 {prog} 졸업요건 요약\n- 총 이수학점: {total}학점\n- 전공 이수학점: {major}학점"
            except Exception:
                msg = "졸업요건 정보를 불러왔습니다."
            return {
                "message": msg,
                "requirements": req,
                "show_requirements": True,
                "_mcp_tools_used": tools_used,
            }

        # 실패 시 누적 → 일반 빌더로 메시지 구성 시도
        _accumulate_results(accumulated_results, "get_requirements", res or {})
        result = _build_final_result("", accumulated_results)
        result["_mcp_tools_used"] = tools_used
        if not result.get("message"):
            result["message"] = res.get("error") if isinstance(res, dict) else "졸업요건 조회에 실패했습니다."
        return result

    # 그 외는 Fallback 없음
    return None


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
