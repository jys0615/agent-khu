#!/usr/bin/env python3
"""
Agent KHU 자동 데이터 수집 스크립트 (Python)
"""
import os
import time
import requests
from pathlib import Path


# 설정
BACKEND_URL = "http://localhost:8000/api/chat"
TOKEN = os.getenv("ANTHROPIC_API_KEY", "")
QUESTIONS_FILE = Path(__file__).parent / "questions.txt"
DELAY = 3  # 초


def load_questions():
    """질문 파일 로드"""
    if not QUESTIONS_FILE.exists():
        print(f"❌ {QUESTIONS_FILE} 파일이 없습니다!")
        return []
    
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def send_question(question: str, index: int, total: int):
    """질문 전송"""
    print(f"\n[{index}/{total}] 질문: {question}")
    
    try:
        response = requests.post(
            BACKEND_URL,
            json={"message": question},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("  ✅ 성공")
            return True
        else:
            print(f"  ❌ 실패 (status: {response.status_code})")
            return False
    
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False


def main():
    print("🤖 Agent KHU 자동 데이터 수집 시작")
    print(f"📁 질문 파일: {QUESTIONS_FILE}\n")
    
    # 질문 로드
    questions = load_questions()
    if not questions:
        return
    
    total = len(questions)
    success = 0
    fail = 0
    
    # 질문 전송
    for i, question in enumerate(questions, 1):
        if send_question(question, i, total):
            success += 1
        else:
            fail += 1
        
        # 다음 요청 전 대기
        if i < total:
            print(f"  ⏳ {DELAY}초 대기 중...")
            time.sleep(DELAY)
    
    # 최종 결과
    print("\n" + "="*40)
    print("✅ 완료!")
    print(f"  총 질문: {total}")
    print(f"  성공: {success}")
    print(f"  실패: {fail}")
    print("="*40)
    print("\n📊 통계 확인: python3 show_stats.py")
    print("📦 데이터 추출: python3 extract_training_data.py")


if __name__ == "__main__":
    main()