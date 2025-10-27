#!/usr/bin/env python3
"""
Curriculum MCP Server
소프트웨어융합대학 교과과정 정보 제공
"""

import asyncio
import json
from pathlib import Path
from typing import Any, List, Dict
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# 데이터 파일 경로
DATA_DIR = Path(__file__).parent / "data"
CURRICULUM_FILE = DATA_DIR / "curriculum_data.json"

class CurriculumMCPServer:
    def __init__(self):
        self.server = Server("curriculum-mcp")
        self.curriculum_data: Dict[str, Any] = {}
        self._setup_handlers()
        self._load_data()
    
    def _load_data(self):
        """교과과정 데이터 로드"""
        if CURRICULUM_FILE.exists():
            with open(CURRICULUM_FILE, 'r', encoding='utf-8') as f:
                self.curriculum_data = json.load(f)
            print(f"✅ 교과과정 데이터 로드 완료: {len(self.curriculum_data)}개 연도")
        else:
            print("⚠️ 교과과정 데이터 파일이 없습니다. 스크래퍼를 먼저 실행하세요.")
            self.curriculum_data = {}
    
    def _setup_handlers(self):
        """MCP 핸들러 설정"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """사용 가능한 리소스 목록"""
            resources = []
            
            for year in self.curriculum_data.keys():
                resources.append(
                    Resource(
                        uri=f"curriculum://{year}",
                        name=f"{year}학년도 교과과정",
                        description=f"소프트웨어융합대학 {year}학년도 교과과정",
                        mimeType="application/json"
                    )
                )
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """리소스 내용 읽기"""
            # curriculum://2024 형식
            year = uri.split("//")[-1]
            
            if year in self.curriculum_data:
                return json.dumps(self.curriculum_data[year], ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"해당 연도의 교과과정이 없습니다: {year}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """사용 가능한 도구 목록"""
            return [
                Tool(
                    name="search_courses",
                    description="과목명 또는 과목코드로 교과과정 검색",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 과목명 또는 과목코드"
                            },
                            "year": {
                                "type": "string",
                                "description": "학년도 (선택사항, 예: 2024)",
                                "default": "latest"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_curriculum",
                    description="특정 학년도의 전체 교과과정 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "year": {
                                "type": "string",
                                "description": "학년도 (예: 2024)"
                            }
                        },
                        "required": ["year"]
                    }
                ),
                Tool(
                    name="get_course_by_code",
                    description="과목코드로 특정 과목 상세 정보 조회",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "과목코드 (예: SWE001)"
                            },
                            "year": {
                                "type": "string",
                                "description": "학년도 (선택사항)",
                                "default": "latest"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="get_courses_by_semester",
                    description="특정 학기에 개설되는 과목 목록 조회",
                    inputSchema={
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
                ),
                Tool(
                    name="refresh_curriculum",
                    description="교과과정 데이터 갱신 (스크래퍼 실행)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """도구 실행"""
            
            if name == "search_courses":
                return await self._search_courses(arguments)
            
            elif name == "get_curriculum":
                return await self._get_curriculum(arguments)
            
            elif name == "get_course_by_code":
                return await self._get_course_by_code(arguments)
            
            elif name == "get_courses_by_semester":
                return await self._get_courses_by_semester(arguments)
            
            elif name == "refresh_curriculum":
                return await self._refresh_curriculum()
            
            else:
                raise ValueError(f"알 수 없는 도구: {name}")
    
    async def _search_courses(self, args: dict) -> List[TextContent]:
        """과목 검색"""
        query = args.get("query", "").lower()
        year = args.get("year", "latest")
        
        if year == "latest":
            year = max(self.curriculum_data.keys())
        
        if year not in self.curriculum_data:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "found": False,
                    "message": f"{year}학년도 데이터가 없습니다."
                }, ensure_ascii=False)
            )]
        
        courses = self.curriculum_data[year].get("courses", [])
        results = []
        
        for course in courses:
            if (query in course.get("name", "").lower() or 
                query in course.get("code", "").lower()):
                results.append(course)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "found": len(results) > 0,
                "count": len(results),
                "year": year,
                "courses": results
            }, ensure_ascii=False, indent=2)
        )]
    
    async def _get_curriculum(self, args: dict) -> List[TextContent]:
        """전체 교과과정 조회"""
        year = args.get("year")
        
        if year not in self.curriculum_data:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "found": False,
                    "message": f"{year}학년도 데이터가 없습니다.",
                    "available_years": list(self.curriculum_data.keys())
                }, ensure_ascii=False)
            )]
        
        return [TextContent(
            type="text",
            text=json.dumps(self.curriculum_data[year], ensure_ascii=False, indent=2)
        )]
    
    async def _get_course_by_code(self, args: dict) -> List[TextContent]:
        """과목코드로 조회"""
        code = args.get("code", "").upper()
        year = args.get("year", "latest")
        
        if year == "latest":
            year = max(self.curriculum_data.keys())
        
        if year not in self.curriculum_data:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "found": False,
                    "message": f"{year}학년도 데이터가 없습니다."
                }, ensure_ascii=False)
            )]
        
        courses = self.curriculum_data[year].get("courses", [])
        
        for course in courses:
            if course.get("code", "").upper() == code:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "found": True,
                        "course": course
                    }, ensure_ascii=False, indent=2)
                )]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "found": False,
                "message": f"과목코드 {code}를 찾을 수 없습니다."
            }, ensure_ascii=False)
        )]
    
    async def _get_courses_by_semester(self, args: dict) -> List[TextContent]:
        """학기별 과목 조회"""
        semester = args.get("semester")
        year = args.get("year", "latest")
        
        if year == "latest":
            year = max(self.curriculum_data.keys())
        
        if year not in self.curriculum_data:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "found": False,
                    "message": f"{year}학년도 데이터가 없습니다."
                }, ensure_ascii=False)
            )]
        
        courses = self.curriculum_data[year].get("courses", [])
        filtered = [c for c in courses if c.get("semester") == semester]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "found": len(filtered) > 0,
                "semester": semester,
                "year": year,
                "count": len(filtered),
                "courses": filtered
            }, ensure_ascii=False, indent=2)
        )]
    
    async def _refresh_curriculum(self) -> List[TextContent]:
        """교과과정 데이터 갱신"""
        try:
            # 스크래퍼 실행
            import subprocess
            scraper_path = Path(__file__).parent / "scrapers" / "curriculum_scraper.py"
            
            result = subprocess.run(
                ["python3", str(scraper_path)],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                # 데이터 재로드
                self._load_data()
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": "교과과정 데이터 갱신 완료",
                        "years": list(self.curriculum_data.keys())
                    }, ensure_ascii=False)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": result.stderr
                    }, ensure_ascii=False)
                )]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                }, ensure_ascii=False)
            )]
    
    async def run(self):
        """서버 실행"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="curriculum-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )


def main():
    """메인 함수"""
    server = CurriculumMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()