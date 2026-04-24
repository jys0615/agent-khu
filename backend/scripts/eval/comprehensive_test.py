import json
import time
import pathlib
import subprocess
from datetime import datetime


API_BASE = "http://localhost:8000"
STUDENT_ID = "2019110635"
PASSWORD = "garen@0302"


def login() -> str:
    resp = subprocess.check_output([
        'curl','-s','-X','POST', f'{API_BASE}/api/auth/login',
        '-H','Content-Type: application/x-www-form-urlencoded',
        '-d', f'username={STUDENT_ID}&password={PASSWORD}'
    ], text=True)
    token = json.loads(resp)['access_token']
    return token


def run_chat(token: str, message: str) -> dict:
    payload = json.dumps({"message": message}, ensure_ascii=False)
    start = time.perf_counter()
    resp = subprocess.check_output([
        'curl','-s','-X','POST', f'{API_BASE}/api/chat',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', payload
    ], text=True)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    try:
        data = json.loads(resp)
    except Exception:
        data = {"raw": resp}
    return {"latency_ms": elapsed_ms, "response": data}


def build_questions() -> list[dict]:
    q = []
    # 공지 (10)
    q += [
        {"cat": "notice", "q": "컴퓨터공학부 최신 공지 3개 알려줘"},
        {"cat": "notice", "q": "소프트웨어융합학과 최신 공지 5개"},
        {"cat": "notice", "q": "장학 관련 공지 찾아줘"},
        {"cat": "notice", "q": "휴학 공지 있어?"},
        {"cat": "notice", "q": "졸업논문 안내 공지 보여줘"},
        {"cat": "notice", "q": "대회 모집 공지 알려줘"},
        {"cat": "notice", "q": "외국인 유학생 공지 요약"},
        {"cat": "notice", "q": "수강신청 관련 최신 공지"},
        {"cat": "notice", "q": "학사 일정 공지 검색"},
        {"cat": "notice", "q": "캡스톤 공지 있니?"},
    ]

    # 학식 (10)
    q += [
        {"cat": "meal", "q": "오늘 학생회관 학식 뭐 나와?"},
        {"cat": "meal", "q": "오늘 저녁 메뉴 알려줘"},
        {"cat": "meal", "q": "불고기 언제 나와?"},
        {"cat": "meal", "q": "비건 메뉴 있어?"},
        {"cat": "meal", "q": "카레 나오는 날 찾아줘"},
        {"cat": "meal", "q": "이번 주 인기 메뉴 추천"},
        {"cat": "meal", "q": "돈까스 메뉴 검색"},
        {"cat": "meal", "q": "라면 가능한가요?"},
        {"cat": "meal", "q": "학식 가격 알려줘"},
        {"cat": "meal", "q": "학생회관 식당 정보 알려줘"},
    ]

    # 도서관 (10)
    q += [
        {"cat": "library", "q": "국제캠퍼스 도서관 운영시간 알려줘"},
        {"cat": "library", "q": "도서관 좌석 현황 볼 수 있어?"},
        {"cat": "library", "q": "도서관 예약 링크 알려줘"},
        {"cat": "library", "q": "시험기간 연장 운영하니?"},
        {"cat": "library", "q": "도서관 위치와 전화번호 알려줘"},
        {"cat": "library", "q": "열람실 좌석 예약 방법 알려줘"},
        {"cat": "library", "q": "서울 캠퍼스 도서관도 알려줘"},
        {"cat": "library", "q": "전자자료실 이용 가능 시간"},
        {"cat": "library", "q": "도서관 이용 수칙 요약해줘"},
        {"cat": "library", "q": "노트북대여 가능해?"},
    ]

    # 강의실 (5)
    q += [
        {"cat": "classroom", "q": "전자정보대학관 312 어디야?"},
        {"cat": "classroom", "q": "컴퓨터공학 실습실 위치 알려줘"},
        {"cat": "classroom", "q": "엘리베이터 있는 강의실이 어디야?"},
        {"cat": "classroom", "q": "교수님 연구실 찾고 싶어"},
        {"cat": "classroom", "q": "강의실 201 가는 길 알려줘"},
    ]

    # 교과과정/졸업요건 (10)
    q += [
        {"cat": "curriculum", "q": "자료구조 교과과정 과목 있어?"},
        {"cat": "curriculum", "q": "2024년 1학기 소프트웨어융합대학 교과과정 과목 보여줘"},
        {"cat": "curriculum", "q": "전공 필수 과목만 모아서 보여줘"},
        {"cat": "curriculum", "q": "AI 관련 과목 찾아줘"},
        {"cat": "curriculum", "q": "클라우드 수업 있어?"},
        {"cat": "curriculum", "q": "프로그래밍언어론 개설 여부"},
        {"cat": "curriculum", "q": "졸업요건 알려줘"},
        {"cat": "curriculum", "q": "졸업 진행도 평가해줘: CSE103,CSE204,CSE305 이수"},
        {"cat": "curriculum", "q": "프로그램 목록 보여줘"},
        {"cat": "curriculum", "q": "1학기에만 여는 과목이 뭐야?"},
    ]

    # 일반 안내 (5)
    q += [
        {"cat": "general", "q": "컴퓨터공학부 소개 간단히 해줘"},
        {"cat": "general", "q": "전공 추천 트랙 알려줘"},
        {"cat": "general", "q": "코딩 스터디 어떻게 시작해?"},
        {"cat": "general", "q": "시험기간 공부 팁"},
        {"cat": "general", "q": "취업 준비 로드맵"},
    ]

    return q


def derive_metrics(item: dict) -> dict:
    r = item.get("response", {})
    msg = r.get("message", "") or ""
    metrics = {
        "message_len": len(msg),
        "has_notices": bool(r.get("notices")),
        "has_meals": bool(r.get("meals")),
        "has_library_info": bool(r.get("show_library_info")) or bool(r.get("library_info")),
        "has_curriculum": bool(r.get("curriculum_courses")) or bool(r.get("courses")),
        "error": r.get("error") or r.get("error_message")
    }
    return metrics


def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    logs_dir = root / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    token = login()
    questions = build_questions()

    results = []
    start_all = time.perf_counter()
    for idx, item in enumerate(questions, 1):
        out = run_chat(token, item["q"])
        metrics = derive_metrics(out)
        results.append({
            "idx": idx,
            "category": item["cat"],
            "question": item["q"],
            "latency_ms": out["latency_ms"],
            "metrics": metrics,
            "response": out["response"],
        })

    total_ms = int((time.perf_counter() - start_all) * 1000)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_questions": len(questions),
        "total_time_ms": total_ms,
        "avg_latency_ms": int(sum(r["latency_ms"] for r in results) / len(results)),
        "by_category": {},
    }

    # 카테고리 통계
    from collections import defaultdict
    cat = defaultdict(list)
    for r in results:
        cat[r["category"]].append(r["latency_ms"])
    for k, v in cat.items():
        summary["by_category"][k] = {
            "count": len(v),
            "avg_latency_ms": int(sum(v)/len(v)),
            "p95_latency_ms": sorted(v)[int(len(v)*0.95)-1] if v else 0,
        }

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_json = logs_dir / f'comprehensive_run_{ts}.json'
    out_txt = logs_dir / f'comprehensive_summary_{ts}.txt'

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({"summary": summary, "items": results}, f, ensure_ascii=False, indent=2)

    # 간략 텍스트 요약
    lines = [
        f"총 {summary['total_questions']}문항, 총 {summary['total_time_ms']}ms, 평균 {summary['avg_latency_ms']}ms",
        "카테고리별 평균 지연(ms):" 
    ]
    for k, v in summary["by_category"].items():
        lines.append(f" - {k}: avg {v['avg_latency_ms']} (p95 {v['p95_latency_ms']})")
    lines.append("")
    for r in results:
        lines.append(f"[{r['category']}] {r['question']} -> {r['latency_ms']}ms, msg_len={r['metrics']['message_len']}")

    out_txt.write_text("\n".join(lines), encoding='utf-8')

    print(f"saved: {out_json}")
    print(f"saved: {out_txt}")


if __name__ == '__main__':
    main()
"""
종합 MCP 테스트 스크립트
모든 MCP 서버를 총동원한 50개 질문 테스트
"""
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
import statistics

# 로그인 토큰 발급
def get_token():
    result = subprocess.check_output([
        'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/auth/login',
        '-H', 'Content-Type: application/x-www-form-urlencoded',
        '-d', 'username=2019110635&password=garen@0302'
    ], text=True)
    return json.loads(result)['access_token']

# 질문 실행 및 측정
def execute_query(token, question):
    payload = json.dumps({"message": question}, ensure_ascii=False)
    
    start_time = time.time()
    try:
        result = subprocess.check_output([
            'curl', '-s', '-X', 'POST', 'http://localhost:8000/api/chat',
            '-H', f'Authorization: Bearer {token}',
            '-H', 'Content-Type: application/json',
            '-d', payload,
            '--max-time', '20'
        ], text=True, timeout=25)
        
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        try:
            parsed = json.loads(result)
            success = True
            error = None
        except Exception as e:
            parsed = {"raw": result}
            success = False
            error = str(e)
        
        # MCP 툴 사용 추출
        mcp_tools = []
        if parsed.get('notices'):
            mcp_tools.append('notice')
        if parsed.get('meals'):
            mcp_tools.append('meal')
        if parsed.get('library_info') or parsed.get('library_seats'):
            mcp_tools.append('library')
        if parsed.get('curriculum_courses') or parsed.get('requirements'):
            mcp_tools.append('curriculum')
        if parsed.get('courses'):
            mcp_tools.append('course')
        if parsed.get('classroom'):
            mcp_tools.append('classroom')
        
        return {
            "question": question,
            "response": parsed,
            "latency_ms": latency_ms,
            "latency_sec": round(latency_ms / 1000, 2),
            "success": success,
            "error": error,
            "response_length": len(parsed.get('message', '')),
            "mcp_tools_used": list(set(mcp_tools)),
            "has_structured_data": any([
                parsed.get('notices'),
                parsed.get('meals'),
                parsed.get('library_info'),
                parsed.get('curriculum_courses'),
                parsed.get('courses'),
                parsed.get('classroom')
            ]),
            "timestamp": datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {
            "question": question,
            "response": {"error": "timeout"},
            "latency_ms": 25000,
            "latency_sec": 25.0,
            "success": False,
            "error": "Request timeout (25s)",
            "response_length": 0,
            "mcp_tools_used": [],
            "has_structured_data": False,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "question": question,
            "response": {"error": str(e)},
            "latency_ms": 0,
            "latency_sec": 0,
            "success": False,
            "error": str(e),
            "response_length": 0,
            "mcp_tools_used": [],
            "has_structured_data": False,
            "timestamp": datetime.now().isoformat()
        }

# 50개 테스트 질문 (다양한 MCP 활용) - 빠른 버전
questions = [
    # Notice MCP (8개)
    "컴공 최신 공지 3개",
    "소융과 공지 2개",
    "전자공학과 공지",
    "장학금 공지 있어?",
    "졸업 관련 공지",
    "취업 공지",
    "대회 공지",
    "수강신청 공지",
    
    # Meal MCP (8개)
    "오늘 학식",
    "점심 메뉴",
    "저녁 학식",
    "돈까스 언제?",
    "김치찌개 나와?",
    "치킨 메뉴",
    "학식 가격",
    "식당 시간",
    
    # Library MCP (8개)
    "도서관 운영시간",
    "서울캠 도서관",
    "중앙도서관 위치",
    "도서관 전화번호",
    "도서관 층별 안내",
    "도서관 평일 시간",
    "도서관 주말",
    "좌석 예약 방법",
    
    # Curriculum MCP (8개)
    "2024년 1학기 교과과정",
    "2학기 개설 과목",
    "커리큘럼",
    "전공필수",
    "졸업요건",
    "전공 핵심",
    "1학기 과목 추천",
    "졸업 학점",
    
    # Course MCP (9개)
    "컴공 과목",
    "소융과 과목",
    "딥러닝 과목",
    "웹프로그래밍",
    "알고리즘 수업",
    "자료구조 과목",
    "데이터베이스",
    "운영체제",
    "네트워크 과목",
    
    # Classroom MCP (9개)
    "전자정보대",
    "401호",
    "교수연구실",
    "편의시설",
    "전정대 층수",
    "강의실 찾기",
    "201호 위치",
    "컴실 어디",
    "실습실"
]

def main():
    print("=" * 60)
    print("🚀 종합 MCP 테스트 시작")
    print("=" * 60)
    print(f"📊 총 질문 수: {len(questions)}개")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 토큰 발급
    print("\n🔑 로그인 토큰 발급 중...")
    token = get_token()
    print("✅ 토큰 발급 완료")
    
    # 질문 실행
    results = []
    for idx, question in enumerate(questions, 1):
        print(f"\n[{idx}/{len(questions)}] 질문: {question}")
        result = execute_query(token, question)
        results.append(result)
        
        status = "✅ 성공" if result['success'] else "❌ 실패"
        print(f"    {status} | {result['latency_ms']}ms | MCP: {', '.join(result['mcp_tools_used']) or 'None'}")
        
        # 진행 표시
        if idx % 10 == 0:
            print(f"\n📊 진행률: {idx}/{len(questions)} ({round(idx/len(questions)*100, 1)}%)")
        
        # 속도 제한 방지 (간격 줄임)
        time.sleep(0.2)
    
    # 통계 계산
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    latencies = [r['latency_ms'] for r in successful]
    avg_latency = statistics.mean(latencies) if latencies else 0
    median_latency = statistics.median(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    
    mcp_usage = {}
    for result in successful:
        for mcp in result['mcp_tools_used']:
            mcp_usage[mcp] = mcp_usage.get(mcp, 0) + 1
    
    summary = {
        "test_info": {
            "total_questions": len(questions),
            "success_count": len(successful),
            "failure_count": len(failed),
            "success_rate": round(len(successful) / len(questions) * 100, 2),
            "start_time": results[0]['timestamp'] if results else None,
            "end_time": results[-1]['timestamp'] if results else None
        },
        "latency_stats": {
            "average_ms": round(avg_latency, 2),
            "median_ms": round(median_latency, 2),
            "min_ms": min_latency,
            "max_ms": max_latency,
            "average_sec": round(avg_latency / 1000, 2),
            "median_sec": round(median_latency / 1000, 2)
        },
        "mcp_usage": mcp_usage,
        "response_stats": {
            "avg_response_length": round(statistics.mean([r['response_length'] for r in successful]), 2) if successful else 0,
            "structured_data_count": len([r for r in successful if r['has_structured_data']]),
            "structured_data_rate": round(len([r for r in successful if r['has_structured_data']]) / len(successful) * 100, 2) if successful else 0
        }
    }
    
    # 결과 저장
    output = {
        "summary": summary,
        "detailed_results": results
    }
    
    output_path = Path('/Users/jung-yoonsuh/Desktop/agent-khu/logs/comprehensive_test_results.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    
    # 요약 리포트 생성
    report_lines = [
        "=" * 80,
        "📊 종합 MCP 테스트 결과 리포트",
        "=" * 80,
        "",
        "## 📈 전체 통계",
        f"- 총 질문 수: {summary['test_info']['total_questions']}개",
        f"- 성공: {summary['test_info']['success_count']}개 ({summary['test_info']['success_rate']}%)",
        f"- 실패: {summary['test_info']['failure_count']}개",
        "",
        "## ⏱️ 응답 속도",
        f"- 평균: {summary['latency_stats']['average_sec']}초 ({summary['latency_stats']['average_ms']}ms)",
        f"- 중앙값: {summary['latency_stats']['median_sec']}초 ({summary['latency_stats']['median_ms']}ms)",
        f"- 최소: {summary['latency_stats']['min_ms']}ms",
        f"- 최대: {summary['latency_stats']['max_ms']}ms",
        "",
        "## 🔧 MCP 서버 사용 통계",
    ]
    
    for mcp, count in sorted(mcp_usage.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"- {mcp}: {count}회")
    
    report_lines.extend([
        "",
        "## 📝 응답 품질",
        f"- 평균 응답 길이: {summary['response_stats']['avg_response_length']}자",
        f"- 구조화된 데이터 포함: {summary['response_stats']['structured_data_count']}개 ({summary['response_stats']['structured_data_rate']}%)",
        "",
        "## ❌ 실패한 질문들",
    ])
    
    for result in failed:
        report_lines.append(f"- {result['question']}: {result['error']}")
    
    report_lines.extend([
        "",
        "=" * 80,
        f"✅ 테스트 완료 | 결과 저장: {output_path}",
        "=" * 80
    ])
    
    report = "\n".join(report_lines)
    
    report_path = Path('/Users/jung-yoonsuh/Desktop/agent-khu/logs/comprehensive_test_report.txt')
    report_path.write_text(report)
    
    print("\n" + report)
    print(f"\n📁 상세 결과 JSON: {output_path}")
    print(f"📄 요약 리포트: {report_path}")

if __name__ == "__main__":
    main()
