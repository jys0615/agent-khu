#!/usr/bin/env python3
"""
Agent KHU 평가 자동화 스크립트
질문을 일괄로 API에 전송하고 응답/로그를 수집
"""
import asyncio
import aiohttp
import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import argparse

# 현재 경로 설정
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# 테스트 질문 파일 경로
QUESTIONS_FILE = SCRIPT_DIR / "evaluation_questions.json"
OUTPUT_FILE = SCRIPT_DIR / "evaluation_results_raw.json"

# API 설정
API_URL = "http://localhost:8000/api/chat"
AUTH_URL = "http://localhost:8000/api/auth/register"

# 테스트용 기본 토큰 (또는 익명)
DEMO_USER = {
    "student_id": "9999999",
    "password": "eval_test_pass_123",
    "name": "평가테스트",
    "department": "컴퓨터공학과",
    "admission_year": 2024,
    "campus": "서울"
}

class EvaluationRunner:
    def __init__(self, num_questions: int = None, output_file: Path = OUTPUT_FILE):
        self.num_questions = num_questions
        self.output_file = output_file
        self.results = []
        self.token = None
        self.session = None
    
    async def get_or_create_token(self) -> str:
        """테스트 계정 토큰 발급 또는 재사용"""
        if self.token:
            return self.token
        
        try:
            async with aiohttp.ClientSession() as session:
                # 회원가입 시도 (이미 있으면 실패해도 괜찮음)
                try:
                    async with session.post(AUTH_URL, json=DEMO_USER, timeout=5) as resp:
                        if resp.status == 201:
                            data = await resp.json()
                            self.token = data.get("access_token")
                            print(f"✅ 새 테스트 계정 생성: {DEMO_USER['student_id']}")
                            return self.token
                except:
                    pass
                
                # 기존 계정으로 로그인
                login_data = {
                    "username": DEMO_USER["student_id"],
                    "password": DEMO_USER["password"]
                }
                async with session.post(
                    "http://localhost:8000/api/auth/login",
                    data=login_data,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.token = data.get("access_token")
                        print(f"✅ 기존 계정으로 로그인: {DEMO_USER['student_id']}")
                        return self.token
        except Exception as e:
            print(f"⚠️ 토큰 발급 실패: {e}")
            print("💡 익명으로 계속 진행합니다.")
        
        return None
    
    async def send_question(self, question: str, q_id: int) -> Dict[str, Any]:
        """단일 질문 전송"""
        try:
            start_time = time.time()
            
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            async with self.session.post(
                API_URL,
                json={"message": question},
                headers=headers,
                timeout=30
            ) as resp:
                latency_ms = int((time.time() - start_time) * 1000)
                
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "id": q_id,
                        "question": question,
                        "status": "success",
                        "latency_ms": latency_ms,
                        "response": data.get("message", ""),
                        "tools_used": data.get("tool_calls", []),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "id": q_id,
                        "question": question,
                        "status": "error",
                        "latency_ms": latency_ms,
                        "error": f"HTTP {resp.status}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
        
        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "id": q_id,
                "question": question,
                "status": "timeout",
                "latency_ms": latency_ms,
                "error": "Request timeout (30s)",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "id": q_id,
                "question": question,
                "status": "error",
                "latency_ms": latency_ms,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run(self):
        """평가 실행"""
        print("=" * 70)
        print("Agent KHU 평가 자동화")
        print("=" * 70)
        
        # 질문 로드
        if not QUESTIONS_FILE.exists():
            print(f"❌ 질문 파일을 찾을 수 없습니다: {QUESTIONS_FILE}")
            return False
        
        with open(QUESTIONS_FILE) as f:
            data = json.load(f)
            questions = data.get("questions", [])
        
        # 질문 수 제한
        if self.num_questions:
            questions = questions[:self.num_questions]
        
        print(f"📋 총 {len(questions)}개 질문 준비됨")
        
        # 토큰 확보
        print("\n🔐 인증 준비 중...")
        token = await self.get_or_create_token()
        if token:
            print(f"✅ 토큰 확보: {token[:20]}...")
        else:
            print("⚠️ 익명으로 진행합니다.")
        
        # 질문 전송
        print(f"\n🚀 질문 전송 시작 (평균 응답 시간: ~2-5초/질문)\n")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            for idx, q_data in enumerate(questions, 1):
                question = q_data.get("text", "")
                q_id = q_data.get("id", idx)
                domain = q_data.get("domain", "unknown")
                
                # 진행 표시
                print(f"[{idx:2d}/{len(questions)}] ({domain:8s}) ", end="", flush=True)
                
                result = await self.send_question(question, q_id)
                self.results.append({**result, "domain": domain})
                
                # 상태 표시
                status = result.get("status", "unknown")
                latency = result.get("latency_ms", 0)
                
                if status == "success":
                    print(f"✅ {latency}ms")
                elif status == "timeout":
                    print(f"⏱️ TIMEOUT")
                else:
                    print(f"❌ {status}")
                
                # 너무 빠른 연속 요청 방지
                await asyncio.sleep(0.5)
        
        # 결과 저장
        print(f"\n💾 결과 저장 중: {self.output_file}")
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 간단한 통계
        self._print_summary()
        
        return True
    
    def _print_summary(self):
        """간단한 통계 출력"""
        print("\n" + "=" * 70)
        print("⚡ 빠른 통계")
        print("=" * 70)
        
        success_count = sum(1 for r in self.results if r.get("status") == "success")
        timeout_count = sum(1 for r in self.results if r.get("status") == "timeout")
        error_count = sum(1 for r in self.results if r.get("status") == "error")
        
        total = len(self.results)
        
        print(f"✅ 성공: {success_count}/{total} ({success_count*100//total}%)")
        print(f"⏱️ 타임아웃: {timeout_count}/{total}")
        print(f"❌ 에러: {error_count}/{total}")
        
        if success_count > 0:
            latencies = [r.get("latency_ms", 0) for r in self.results if r.get("status") == "success"]
            if latencies:
                print(f"\n📊 응답 시간 (성공한 요청만):")
                print(f"   최소: {min(latencies)}ms")
                print(f"   평균: {sum(latencies)//len(latencies)}ms")
                print(f"   최대: {max(latencies)}ms")
        
        print(f"\n📁 자세한 결과: {self.output_file}")
        print(f"💡 다음: python3 analyze_metrics.py")


async def main():
    parser = argparse.ArgumentParser(description="Agent KHU 평가 자동화")
    parser.add_argument("--num", type=int, default=None, help="테스트할 질문 수 (기본: 모두)")
    parser.add_argument("--output", type=str, default=None, help="결과 파일 경로")
    args = parser.parse_args()
    
    output_file = Path(args.output) if args.output else OUTPUT_FILE
    
    runner = EvaluationRunner(num_questions=args.num, output_file=output_file)
    success = await runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
