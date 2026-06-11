"""
RAG 초기 시드 데이터 인덱싱 스크립트
경희대 자주 묻는 질문/정보를 khu-rag-knowledge ES 인덱스에 적재

실행: docker exec agent-khu-backend python scripts/seed_rag.py
"""
import asyncio
import sys
import os

sys.path.insert(0, "/app")
os.environ.setdefault("ELASTICSEARCH_URL", "http://elasticsearch:9200")

from app.rag_agent import get_rag_agent

SEED_DOCS = [
    # ── 셔틀버스 ──────────────────────────────────────────────────
    {
        "doc_id": "shuttle-to-station-schedule",
        "category": "shuttle",
        "title": "경희대 국제캠퍼스 → 기흥역 셔틀 시간표",
        "content": (
            "경희대 국제캠퍼스에서 기흥역으로 가는 셔틀버스 시간표입니다.\n"
            "출발 시간: 08:00, 08:30, 09:00, 09:30, 10:00, 11:00, 12:00, 13:00, "
            "14:00, 15:00, 16:00, 17:00, 17:30, 18:00, 18:30, 19:00, 20:00, 21:00, 22:00\n"
            "공식 정보: https://www.khu.ac.kr/kor/bbs/list.do?bbsId=BBSMSTR_000000001905"
        ),
        "metadata": {"source": "static", "campus": "international"},
    },
    {
        "doc_id": "shuttle-to-campus-schedule",
        "category": "shuttle",
        "title": "기흥역 → 경희대 국제캠퍼스 셔틀 시간표",
        "content": (
            "기흥역에서 경희대 국제캠퍼스로 오는 셔틀버스 시간표입니다.\n"
            "출발 시간: 08:10, 08:40, 09:10, 09:40, 10:10, 11:10, 12:10, 13:10, "
            "14:10, 15:10, 16:10, 17:10, 17:40, 18:10, 18:40, 19:10, 20:10, 21:10, 22:10\n"
            "학기 중 기준이며 방학/공휴일에는 변동될 수 있습니다."
        ),
        "metadata": {"source": "static", "campus": "international"},
    },
    # ── 도서관 ────────────────────────────────────────────────────
    {
        "doc_id": "library-global-info",
        "category": "library",
        "title": "경희대 국제캠퍼스 도서관 정보",
        "content": (
            "경희대학교 국제캠퍼스 도서관 정보입니다.\n"
            "위치: 경기도 용인시 기흥구 덕영대로 1732\n"
            "전화: 031-201-3210\n"
            "운영시간: 평일 09:00-22:00, 주말 09:00-18:00\n"
            "좌석 예약: https://library.khu.ac.kr/seat"
        ),
        "metadata": {"source": "static", "campus": "international"},
    },
    {
        "doc_id": "library-seoul-info",
        "category": "library",
        "title": "경희대 서울캠퍼스 중앙도서관 정보",
        "content": (
            "경희대학교 서울캠퍼스 중앙도서관 정보입니다.\n"
            "위치: 서울특별시 동대문구 경희대로 26\n"
            "전화: 02-961-0072\n"
            "운영시간: 24시간 (출입통제구역 제외)\n"
            "열람실: 제1열람실(406석), 제2열람실(326석) 등\n"
            "좌석 예약: https://library.khu.ac.kr/seat"
        ),
        "metadata": {"source": "static", "campus": "seoul"},
    },
    # ── 학식 ──────────────────────────────────────────────────────
    {
        "doc_id": "cafeteria-info",
        "category": "meal",
        "title": "경희대 국제캠퍼스 학생식당 정보",
        "content": (
            "경희대학교 국제캠퍼스 학생회관 학생식당 정보입니다.\n"
            "위치: 학생회관 1층\n"
            "운영시간: 점심 11:30-14:00, 저녁 17:00-18:30\n"
            "가격: 평균 5,000원 (4,500-6,000원)\n"
            "결제: 경희카드, 신용카드, 체크카드, 현금\n"
            "메뉴 확인: https://khucoop.com/35\n"
            "문의: 02-961-0233"
        ),
        "metadata": {"source": "static", "campus": "international"},
    },
    # ── 학사 일정 / 자주 묻는 질문 ──────────────────────────────
    {
        "doc_id": "graduation-credits-general",
        "category": "curriculum",
        "title": "경희대 졸업 이수학점 기준",
        "content": (
            "경희대학교 졸업에 필요한 총 이수학점은 일반적으로 130-140학점입니다.\n"
            "컴퓨터공학과(KHU-CSE) 기준: 총 140학점 (전공필수 45학점 이상, 전공선택 33학점 이상, 교양 18학점 이상)\n"
            "정확한 졸업요건은 입학년도와 학과에 따라 다를 수 있으며, 학과 홈페이지 또는 교학처에서 확인하세요."
        ),
        "metadata": {"source": "static"},
    },
    {
        "doc_id": "klas-info",
        "category": "academic",
        "title": "경희대 KLAS (학사정보시스템) 안내",
        "content": (
            "경희대학교 학사정보시스템(KLAS) 주소: https://klas.khu.ac.kr\n"
            "수강신청, 성적 조회, 졸업 심사, 각종 증명서 발급 등을 처리할 수 있습니다.\n"
            "수강신청 시스템: https://sugang.khu.ac.kr\n"
            "포털 시스템: https://portal.khu.ac.kr"
        ),
        "metadata": {"source": "static"},
    },
    {
        "doc_id": "campus-map-international",
        "category": "campus",
        "title": "경희대 국제캠퍼스 주요 건물 위치",
        "content": (
            "경희대학교 국제캠퍼스 주요 건물:\n"
            "- 전자정보대학관: 소프트웨어융합대학 강의 및 연구실 (위치: 캠퍼스 중심부)\n"
            "- 학생회관: 학생식당, 편의시설\n"
            "- 도서관: 열람실 및 자료실\n"
            "- 체육관: 스포츠 시설\n"
            "캠퍼스 주소: 경기도 용인시 기흥구 덕영대로 1732"
        ),
        "metadata": {"source": "static", "campus": "international"},
    },
    {
        "doc_id": "tuition-scholarship-general",
        "category": "scholarship",
        "title": "경희대 장학금 안내",
        "content": (
            "경희대학교 장학금 종류:\n"
            "- 성적우수 장학금: 직전 학기 성적 기준 지급\n"
            "- 국가장학금(한국장학재단): 소득분위별 지원, 복지로 신청\n"
            "- 근로장학금: 교내 근로 후 시간당 지급\n"
            "- 교외장학금: 각종 기업/재단 장학금\n"
            "장학금 신청 및 공고: KLAS(https://klas.khu.ac.kr) 또는 학과 공지사항 확인\n"
            "장학처 문의: 031-201-2045 (국제캠퍼스)"
        ),
        "metadata": {"source": "static"},
    },
    {
        "doc_id": "swcon-department-info",
        "category": "department",
        "title": "경희대 소프트웨어융합대학 소개",
        "content": (
            "경희대학교 소프트웨어융합대학은 국제캠퍼스에 위치합니다.\n"
            "소속 학과:\n"
            "- 소프트웨어융합학과: SW 개발 및 융합 전공\n"
            "- 컴퓨터공학부\n"
            "  - 컴퓨터공학과: 시스템, 알고리즘, 네트워크 전공\n"
            "  - 인공지능학과: 머신러닝, 딥러닝, AI 전공\n"
            "학과 사무실: 전자정보대학관\n"
            "학과 홈페이지: http://swcon.khu.ac.kr (소프트웨어융합학과)"
        ),
        "metadata": {"source": "static"},
    },
]


async def main():
    print(f"RAG 시드 데이터 인덱싱 시작: {len(SEED_DOCS)}건")
    rag = get_rag_agent()
    await rag.initialize()

    # ES 직접 연결 (enabled=False여도 인덱싱 가능하도록)
    from elasticsearch import AsyncElasticsearch
    es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    es = AsyncElasticsearch([es_url])

    from datetime import datetime, timezone
    actions = []
    now = datetime.now(timezone.utc).isoformat()
    for doc in SEED_DOCS:
        actions.append({"index": {"_index": "khu-rag-knowledge", "_id": doc["doc_id"]}})
        actions.append({
            "doc_id":     doc["doc_id"],
            "category":   doc["category"],
            "title":      doc["title"],
            "content":    doc["content"],
            "metadata":   doc.get("metadata", {}),
            "indexed_at": now,
        })

    response = await es.bulk(operations=actions, refresh=True)
    errors = [item for item in response.get("items", []) if "error" in item.get("index", {})]
    indexed = len(SEED_DOCS) - len(errors)

    print(f"✅ 인덱싱 완료: {indexed}/{len(SEED_DOCS)}건")
    if errors:
        print(f"❌ 실패: {len(errors)}건")
        for e in errors:
            print(f"  - {e}")

    # 확인
    count = await es.count(index="khu-rag-knowledge")
    print(f"현재 인덱스 총 문서 수: {count['count']}건")
    await es.close()


if __name__ == "__main__":
    asyncio.run(main())
