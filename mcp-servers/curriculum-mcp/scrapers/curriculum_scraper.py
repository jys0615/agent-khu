#!/usr/bin/env python3
"""
소프트웨어융합대학 교과과정 PDF 스크래퍼
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
import PyPDF2
from typing import List, Dict, Any
import io

class CurriculumScraper:
    def __init__(self):
        self.base_url = "https://software.khu.ac.kr"
        self.list_url = f"{self.base_url}/software/user/bbs/BMSR00048/list.do?menuNo=1700015"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
    def get_pdf_links(self) -> List[Dict[str, str]]:
        """교과과정 PDF 링크 목록 가져오기"""
        response = requests.get(self.list_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_links = []
        
        # JavaScript view() 함수에서 ID 추출
        # 예: javascript:view('412977');
        for link in soup.find_all('a', href=re.compile(r"javascript:view")):
            text = link.get_text(strip=True)
            href = link.get('href')
            
            # ID 추출
            match = re.search(r"view\('(\d+)'\)", href)
            if match:
                doc_id = match.group(1)
                year_match = re.search(r'(\d{4})학년도', text)
                
                if year_match:
                    year = year_match.group(1)
                    pdf_links.append({
                        'year': year,
                        'title': text,
                        'doc_id': doc_id,
                        'download_url': f"{self.base_url}/software/user/bbs/BMSR00048/view.do?bbsSeq={doc_id}"
                    })
        
        return sorted(pdf_links, key=lambda x: x['year'], reverse=True)
    
    def download_pdf(self, doc_id: str, year: str) -> bytes:
        """PDF 파일 다운로드"""
        # 실제 다운로드 URL 구성 (사이트 구조에 따라 조정 필요)
        view_url = f"{self.base_url}/software/user/bbs/BMSR00048/view.do?bbsSeq={doc_id}"
        
        # 먼저 상세 페이지 접근
        session = requests.Session()
        response = session.get(view_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 첨부파일 링크 찾기
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if 'download' in href.lower() or href.endswith('.pdf'):
                pdf_url = self.base_url + href if href.startswith('/') else href
                pdf_response = session.get(pdf_url)
                
                if pdf_response.status_code == 200:
                    # PDF 파일 저장
                    pdf_path = self.data_dir / f"curriculum_{year}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"✅ {year}학년도 PDF 다운로드 완료: {pdf_path}")
                    return pdf_response.content
        
        print(f"⚠️ {year}학년도 PDF 다운로드 실패")
        return None
    
    def parse_pdf_text(self, pdf_content: bytes) -> str:
        """PDF에서 텍스트 추출"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"PDF 파싱 에러: {e}")
            return ""
    
    def parse_courses(self, text: str, year: str) -> List[Dict[str, Any]]:
        """텍스트에서 과목 정보 추출"""
        courses = []
        
        # 과목 정보 패턴 (실제 PDF 구조에 맞게 조정 필요)
        # 예: "SWE001 | 프로그래밍기초 | 3학점 | 1학년 1학기"
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 과목코드 패턴 찾기 (예: SWE001, CSE101 등)
            if re.match(r'^[A-Z]{3}\d{3,4}', line):
                parts = line.split('|')
                
                if len(parts) >= 3:
                    course = {
                        'year': year,
                        'code': parts[0].strip(),
                        'name': parts[1].strip() if len(parts) > 1 else '',
                        'credits': self._extract_credits(parts[2]) if len(parts) > 2 else 3,
                        'semester': self._extract_semester(parts[3]) if len(parts) > 3 else '',
                        'prerequisites': []
                    }
                    courses.append(course)
        
        return courses
    
    def _extract_credits(self, text: str) -> int:
        """학점 추출"""
        match = re.search(r'(\d+)\s*학점', text)
        return int(match.group(1)) if match else 3
    
    def _extract_semester(self, text: str) -> str:
        """학기 정보 추출"""
        if '1학기' in text:
            return '1학기'
        elif '2학기' in text:
            return '2학기'
        return ''
    
    def scrape_all(self) -> Dict[str, Any]:
        """모든 교과과정 스크래핑"""
        print("🔍 교과과정 PDF 링크 수집 중...")
        pdf_links = self.get_pdf_links()
        
        all_courses = {}
        
        for link in pdf_links[:3]:  # 최근 3개년도만
            year = link['year']
            doc_id = link['doc_id']
            
            print(f"\n📄 {year}학년도 교과과정 다운로드 중...")
            pdf_content = self.download_pdf(doc_id, year)
            
            if pdf_content:
                print(f"📖 {year}학년도 PDF 파싱 중...")
                text = self.parse_pdf_text(pdf_content)
                
                print(f"🔎 {year}학년도 과목 정보 추출 중...")
                courses = self.parse_courses(text, year)
                
                all_courses[year] = {
                    'year': year,
                    'total_courses': len(courses),
                    'courses': courses,
                    'raw_text': text[:1000]  # 처음 1000자만 저장
                }
                
                print(f"✅ {year}학년도: {len(courses)}개 과목 추출 완료")
        
        # JSON 저장
        output_file = self.data_dir / "curriculum_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_courses, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 데이터 저장 완료: {output_file}")
        return all_courses


if __name__ == "__main__":
    scraper = CurriculumScraper()
    result = scraper.scrape_all()
    
    print(f"\n📊 스크래핑 결과:")
    for year, data in result.items():
        print(f"  {year}학년도: {data['total_courses']}개 과목")