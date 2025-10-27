"""
Course MCP Server - 자동 시간표 조회
로그인 없이 종합시간표 자동 크롤링
"""
import sys
import json
import os
from datetime import datetime
from typing import List, Dict
import asyncio

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Playwright for web scraping
from playwright.async_api import async_playwright

# DB 연결
sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import models

server = Server("course-mcp")

class CourseScraper:
    """수강신청 사이트 크롤러"""
    
    def __init__(self):
        self.base_url = "https://sugang.khu.ac.kr/"
        self.cache = {}
        self.cache_duration = 3600  # 1시간 캐싱
        
    async def get_courses(self, department: str = "소프트웨어융합학과", semester: str = None) -> List[Dict]:
        """
        종합시간표에서 학과별 과목 정보를 자동으로 가져옴
        로그인 불필요!
        """
        # 캐시 확인
        cache_key = f"{department}_{semester}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_duration:
                print(f"📦 캐시된 데이터 반환: {cache_key}")
                return cached_data
        
        print(f"🔍 크롤링 시작: {department} - {semester or '현재학기'}")
        
        async with async_playwright() as p:
            # 헤드리스 모드로 실행 (백그라운드)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 1. 수강신청 사이트 접속
                await page.goto(self.base_url, wait_until="networkidle")
                print("✅ 사이트 접속 완료")
                
                # 2. 종합시간표 조회 페이지로 이동
                # (실제 선택자는 사이트 확인 필요)
                await page.click("text=종합시간표")
                await page.wait_for_load_state("networkidle")
                print("✅ 종합시간표 페이지 이동")
                
                # 3. 학과 선택
                await page.select_option("select#department", department)
                print(f"✅ 학과 선택: {department}")
                
                # 4. 학기 선택 (있다면)
                if semester:
                    await page.select_option("select#semester", semester)
                    print(f"✅ 학기 선택: {semester}")
                
                # 5. 조회 버튼 클릭
                await page.click("button#search")
                await page.wait_for_selector("table.timetable", timeout=10000)
                print("✅ 시간표 데이터 로드 완료")
                
                # 6. 테이블 데이터 파싱
                courses = await page.evaluate('''
                    () => {
                        const rows = document.querySelectorAll('table.timetable tbody tr');
                        return Array.from(rows).map(row => {
                            const cells = row.querySelectorAll('td');
                            return {
                                code: cells[0]?.textContent?.trim() || '',
                                name: cells[1]?.textContent?.trim() || '',
                                professor: cells[2]?.textContent?.trim() || '',
                                credits: cells[3]?.textContent?.trim() || '',
                                time: cells[4]?.textContent?.trim() || '',
                                room: cells[5]?.textContent?.trim() || '',
                                type: cells[6]?.textContent?.trim() || '',  // 이수구분
                                capacity: cells[7]?.textContent?.trim() || '',
                                note: cells[8]?.textContent?.trim() || ''
                            };
                        }).filter(course => course.code);  // 빈 행 제거
                    }
                ''')
                
                print(f"✅ {len(courses)}개 과목 파싱 완료")
                
                # 캐시 저장
                self.cache[cache_key] = (courses, datetime.now())
                
                return courses
                
            except Exception as e:
                print(f"❌ 크롤링 오류: {e}")
                return []
                
            finally:
                await browser.close()
    
    async def search_by_professor(self, professor_name: str) -> List[Dict]:
        """교수명으로 과목 검색"""
        all_courses = await self.get_courses()
        return [c for c in all_courses if professor_name in c.get("professor", "")]
    
    async def search_by_keyword(self, keyword: str, department: str = None) -> List[Dict]:
        """키워드로 과목 검색 (과목명, 과목코드)"""
        courses = await self.get_courses(department) if department else []
        
        keyword_lower = keyword.lower()
        return [
            c for c in courses
            if keyword_lower in c.get("name", "").lower() 
            or keyword_lower in c.get("code", "").lower()
        ]

# Scraper 인스턴스
scraper = CourseScraper()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """MCP 도구 목록"""
    return [
        Tool(
            name="search_courses",
            description="학과별 개설 교과목 자동 조회 (종합시간표)",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "학과명 (예: 소프트웨어융합학과, 컴퓨터공학과)",
                        "default": "소프트웨어융합학과"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "검색 키워드 (과목명, 교수명)"
                    }
                }
            }
        ),
        Tool(
            name="get_professor_courses",
            description="특정 교수의 담당 과목 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "professor": {
                        "type": "string",
                        "description": "교수명"
                    }
                },
                "required": ["professor"]
            }
        ),
        Tool(
            name="get_course_by_code",
            description="과목 코드로 상세 정보 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "과목 코드"
                    }
                },
                "required": ["code"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행 - 자동으로 웹사이트 크롤링"""
    
    try:
        if name == "search_courses":
            # 학과별 전체 과목 조회 (자동 크롤링)
            department = arguments.get("department", "소프트웨어융합학과")
            keyword = arguments.get("keyword")
            
            print(f"🚀 과목 검색 시작: {department}")
            courses = await scraper.get_courses(department)
            
            # 키워드 필터링
            if keyword:
                keyword_lower = keyword.lower()
                courses = [
                    c for c in courses
                    if keyword_lower in c.get("name", "").lower()
                    or keyword_lower in c.get("professor", "").lower()
                    or keyword_lower in c.get("code", "").lower()
                ]
                print(f"🔍 '{keyword}' 검색 결과: {len(courses)}개")
            
            # 결과 정리
            result = {
                "department": department,
                "total": len(courses),
                "courses": courses[:20] if len(courses) > 20 else courses  # 최대 20개
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_professor_courses":
            # 교수별 과목 조회
            professor = arguments.get("professor")
            print(f"👨‍🏫 {professor} 교수 과목 검색")
            
            courses = await scraper.search_by_professor(professor)
            
            result = {
                "professor": professor,
                "total": len(courses),
                "courses": courses
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_course_by_code":
            # 과목 코드로 검색
            code = arguments.get("code")
            courses = await scraper.get_courses()
            
            course = next((c for c in courses if c.get("code") == code), None)
            
            if course:
                return [TextContent(
                    type="text",
                    text=json.dumps(course, ensure_ascii=False, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"과목 코드 {code}를 찾을 수 없습니다"}, ensure_ascii=False)
                )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]

async def main():
    """MCP Server 시작"""
    print("🚀 Course MCP Server 시작")
    print("📚 종합시간표 자동 조회 서버")
    print("-" * 40)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())