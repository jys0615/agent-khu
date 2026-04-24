#!/bin/bash

# Agent KHU 자동 데이터 수집 스크립트

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 설정
BACKEND_URL="http://localhost:8000/api/chat"
TOKEN="${ANTHROPIC_API_KEY}"  # 환경변수에서 가져오거나 직접 입력
QUESTIONS_FILE="questions.txt"
DELAY=3  # 각 요청 사이 대기 시간 (초)

echo -e "${BLUE}🤖 Agent KHU 자동 데이터 수집 시작${NC}"
echo -e "${BLUE}📁 질문 파일: ${QUESTIONS_FILE}${NC}"
echo ""

# 질문 파일 확인
if [ ! -f "$QUESTIONS_FILE" ]; then
    echo -e "${RED}❌ $QUESTIONS_FILE 파일이 없습니다!${NC}"
    exit 1
fi

# 총 질문 개수
TOTAL=$(wc -l < "$QUESTIONS_FILE")
CURRENT=0
SUCCESS=0
FAIL=0

# 질문 파일 읽기
while IFS= read -r question || [ -n "$question" ]; do
    CURRENT=$((CURRENT + 1))
    
    echo -e "${BLUE}[$CURRENT/$TOTAL]${NC} 질문: ${GREEN}$question${NC}"
    
    # API 호출
    response=$(curl -s -X POST "$BACKEND_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"message\": \"$question\"}" \
        --max-time 30)
    
    # 결과 확인
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ 성공${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "  ${RED}❌ 실패${NC}"
        FAIL=$((FAIL + 1))
    fi
    
    # 다음 요청 전 대기
    if [ $CURRENT -lt $TOTAL ]; then
        echo -e "  ⏳ ${DELAY}초 대기 중..."
        sleep $DELAY
    fi
    
    echo ""
done < "$QUESTIONS_FILE"

# 최종 결과
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 완료!${NC}"
echo -e "  총 질문: $TOTAL"
echo -e "  성공: ${GREEN}$SUCCESS${NC}"
echo -e "  실패: ${RED}$FAIL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📊 통계 확인:${NC} python3 show_stats.py"
echo -e "${BLUE}📦 데이터 추출:${NC} python3 extract_training_data.py"