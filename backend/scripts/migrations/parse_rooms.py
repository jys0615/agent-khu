"""
전자정보대학관 공간 데이터 파싱
"""
import re
from typing import List, Dict, Tuple

# 원본 데이터
RAW_DATA = """
B05-1 집기비품 보관실 B01 SW Open Lab. B03 전산관리실/A.I오픈랩 B05 SW실습실 B06 SW융합실습실 B07 SW융합실습실 B08 SW중심대학사업단 B09 Software Creative Lab. B10 유류탱크실 B100-1 복도 B100-2 복도 B100-3 복도 B100-4 복도 B100-5 복도 B114-1 화장실(여) B114-2 화장실(남) B12 발전기실 B13 기계실 b1993A PS실 b1995A ELEV실 b1997A 계단실 b1997B 계단실

100-1 복도 100-2 복도 100-3 복도 100-4 복도 100-5 복도 100-6 방풍실 100-7 복도 100-8 방풍실 101 강의실 102 강의실 102A 화장실(여) 102B 화장실(남) 103 강의실 104 자연과학종합연구원 105 청정실 106-1 자연과학종합연구원 106-2 자연과학종합연구원 106-3 자연과학종합연구원 106-4 자연과학종합연구원 107-1 소프트웨어융합학과 오픈랩 107-2 일반인공지능 연구실 108 복사실 109 자연과학종합연구원 110A 화장실(여) 110B 화장실(남) 111 열람실 112 휴게실(매점) 113 나노에너지소자연구실 113-1 CDC실 114 생체의공학과학생회 115 현대물리실험실(암실) 116 우주과학과학생회 117 물성물리실험실 118 터 119 물성물리실험준비실 120 전자정보대학학생회/응용과학대학학생회 121 수위실 122 광전자및응용광학연구실 122-1 중시계양자전도연구실 123 양자광학연구실 125 전자물리실험실 127 양자정보실험실 129 양자소자연구실 131 공작실1 132A 화장실(여) 132B 화장실(남) 133 물성계산연구실 135 물리학과학생회실 136 강의실 137 강의실 138 응용수학과학생회실 139 반도체물성연구실 140 반도체광공학연구실 141-1 나노전자소자연구실 141-2 나노전자소자연구실 150 수위실(신관) 1993A PS실 1993B EPS실 1993C EPS(서)실 1993D EPS(동)실 1995A ELEV실 1995B ELEV실 1997A 계단실 1997B 계단실 1997C 계단실 1997D 계단실 1997E 계단실

200-1 복도 200-2 복도 200-3 복도 200-4 복도(첨단강의실라운지) 201 전자정보대학학장실 202 산학협력중점교수연구실 202-1 International Scholar연구실 203 전자정보대학행정실 203-2 응용과학대학행정실 203-3 응용과학대학학장실 204 교수휴게실 205 계단강의실 205A 화장실(여) 205B 화장실(남) 206 EE Lab-O 337-1 에너지&포토닉스제어연구실 207 바이오메디칼 오픈랩 208 EE Lab-C 209 바이오메디칼 창의랩 210A 화장실(여) 210B 화장실(남) 211-1 첨단강의실 211-2 현대식강의실 211-3 현대식세미나실 213 응용과학대학 행정실-창고 215 수리계산연습실 217 강의실 218 강의실 219 강의실 220 강의실 221 강의실 223 강의실 225 천체계산실험실 226 강의실 226-1 창고 227 강의실 228A 화장실(여) 228B 화장실(남) 229 우주과학실험실 229-1 글로벌SW융합연구소 233 세상밖으로 235 해오름 237 RaCos 239 Chaos/MUTE 240 소프트웨어융합대학/컴퓨터공학부학생회실 241-1 다솜 241-2 Return 241-3 T.G.Wing 241-4 D.com 241-5 N.E.T 241-6 HACKER 241-7 S/W갤러리 242 MARO 244 호연지기 246 W.W.W 248 얼리버드 250 돌쇠 2993A PS실 2993B EPS실 2993C EPS(서)실 2993D EPS(동)실 2995A ELEV실 2995B ELEV실 2997A 계단실 2997B 계단실 2997C 계단실 2997D 계단실 2997E 계단실

300-1 복도 300-2 복도 300-3 복도 300-4 복도 300-5 복도 300-6 복도 301 조진성교수연구실 303 홍충선교수연구실 305 배성호교수연구실 307 이승규교수연구실 309 세미나실 310 ASIC설계실험실(삭제에정/비품등롤금지) 310-1 나노바이오실험실 310-2 데이터 분석 및 시각 지능 연구실 311 한치근교수연구실 313 허의남교수연구실 314 강형엽교수연구실 315 이영구교수연구실 316 대학원생공동연구실 317 유인태교수연구실 318 황효석교수연구실 319 전석희교수연구실 319A 화장실(여) 319B 화장실(남) 320 IIIXR연구실 321 박광훈교수연구실 322 햅틱스및가상현실연구실 323 이성원교수연구실 323-1 인공지능융합혁신인재양성사업단 324 최진우교수연구실 325-1 비전 및 학습 연구실 325-2 디지털회로실험실 325-3 김정욱교수연구실 325-4 박경문교수연구실 326 NRF기초연구실 327 컴퓨터구조및VLSI연구실1 328A 화장실(여) 328B 화장실(남) 329 Inno-Gallery 330-1 ICT성능검증실험실 330-2 컴퓨터구조및VLSI연구실2 331 지능컴퓨팅및보안연구실ICT성능검증연구센터 332 WINS연구실 333 전파통신실험실1 335 디지털통신연구실 336 전파무반사측정실험실 337 대학원생공동연구실 338 전파통신실험실2 338A 화장실(여) 338B 화장실(남) 339 대학원생공동연구실 340 창고 341 컴퓨터비전 및 인식연구실 343 컴퓨터공학과학생회 345 정보통신연구실 347 알고리즘연구실 348 모바일&임베디드 시스템 연구실 349 데이터및지식공학연구실 350 머신러닝 및 비주얼컴퓨팅 연구실 351 시각인공지능연구실 352 지능네트워킹연구실 3993A PS실 3993B EPS실 3993C EPS(서)실 3993D EPS(동)실 3995A ELEV실 3995B ELEV실 3997A 계단실 3997B 계단실 3997C 계단실 3997D 계단실 3997E 계단실

400-1 복도 400-2 복도 400-3 복도 400-4 복도 400-5 복도 400-6 복도 401 김대원교수연구실 403 박욱교수연구실 405 김상혁교수연구실 407 홍상훈교수연구실 408 최승규교수연구실 409 세미나실 410 최기호교수연구실 411 양자계산이론 연구실 412-1 응용수학연구실 412-2 수학교구실 413 최선호교수연구실 414 수학연습실 415 수학모델링과 해석연구실 416 고한얼교수연구실 417 바이오수학 연구실 418 지능형 무선 네트워크 연구실 419 금융수학연구실 420A 화장실(여) 420B 화장실(남) 421 박준표교수실험실(비선형동역학 연구실) 423 한창용교수연구실 425 김혜현교수연구실 426 송현욱교수연구실 427 이종수교수연구실 428 손종역교수연구실 429 이성훈교수연구실 430 김선경교수연구실 431 이광조교수연구실 432 이민철교수연구실 433 임대영교수연구실 434 이호선교수연구 435 이은상교수연구실 436 자연어처리연구실 437 우주 플라즈마 연구실 439-1 분자생물학실험실 439-2 분자생물학연구실 441 에너지&포토닉스제어연구실 442 건강노화한의학연구실2 443-1 인공지능및로보틱스연구실 443-2 김휘용교수연구실 444 건강노화한의학연구실1 445 강의실 446 AgeTech-Service 연구실 447 한방면역학실험실 447-1 노인약리학실험실 448 단백질유전체연구실 449 영양생화학실험실 449-1 분자질병학실험실1 450-1 샤워실(남) 450-2 화장실(남) 451 공동기기실3 453 공동기기실2 455 실험동물실 456-1 화장실(남) 456-2 화장실(여) 456-3 샤워실(여) 457 공동기기실1 459 저온실 461 의학영양학과 공공기기실 463 영양면역학연구실 465 BK21 AgeTech –Service 교육연구단 행정실 466 영양면역학실험실 467 생리학연구실2 468 생리학연구실1 469 미래식품학과(계약학과) 행정실 470 생유기화학연구실1 471 생유기화학연구실2 473 건강노화연구실 4993A PS실 4993B EPS실 4993C EPS(서)실 4993D EPS(동)실 4995A ELEV실 4995B ELEV실 4997A 계단실 4997B 계단실 4997C 계단실 4997D 계단실 4997E 계단실
"""


def parse_floor(text: str) -> Tuple[str, List[Dict]]:
    """
    층별 데이터 파싱
    """
    # 층 구분
    if text.startswith('B') or text.startswith('b'):
        floor = 'B'
    else:
        floor = text[0]
    
    rooms = []
    
    # 공백으로 분리
    parts = text.split()
    
    i = 0
    while i < len(parts):
        room_code = parts[i]
        
        # 다음 항목들을 이름으로 수집 (다음 코드가 나올 때까지)
        name_parts = []
        i += 1
        while i < len(parts) and not is_room_code(parts[i]):
            name_parts.append(parts[i])
            i += 1
        
        room_name = ' '.join(name_parts)
        
        if room_name:
            rooms.append({
                'code': room_code,
                'name': room_name,
                'floor': floor
            })
    
    return floor, rooms


def is_room_code(text: str) -> bool:
    """
    호실 코드인지 판단
    """
    # B01, 101, 200-1, 1993A 등의 패턴
    patterns = [
        r'^[Bb]?\d+[A-Z]?$',           # 101, B01, 1993A
        r'^[Bb]?\d+-\d+$',             # 100-1, B100-1
        r'^[Bb]?\d+[A-Z]-\d+$',        # 325-1
    ]
    
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False


def classify_room_type(name: str) -> str:
    """
    공간 유형 분류
    """
    name_lower = name.lower()
    
    # 화장실
    if '화장실' in name or '샤워실' in name:
        return 'restroom'
    
    # 강의실
    if '강의실' in name:
        return 'classroom'
    
    # 교수 연구실
    if '교수' in name and '연구실' in name:
        return 'professor_office'
    
    # 일반 연구실
    if '연구실' in name or 'lab' in name_lower or '실험실' in name:
        return 'lab'
    
    # 행정실
    if '행정실' in name or '학장실' in name or '사업단' in name:
        return 'admin_office'
    
    # 학생회실
    if '학생회' in name:
        return 'student_council'
    
    # 세미나실
    if '세미나실' in name:
        return 'seminar_room'
    
    # 복도/계단/엘리베이터
    if any(x in name for x in ['복도', '계단', 'elev', 'ps실', 'eps실']):
        return 'facility'
    
    # 편의시설
    if any(x in name for x in ['휴게실', '매점', '수위실']):
        return 'amenity'
    
    # 창고/기계실 등
    if any(x in name for x in ['창고', '기계실', '발전기', '탱크']):
        return 'utility'
    
    # 동아리방 (한글 이름만 있는 경우)
    if len(name) < 20 and not any(x in name for x in ['실', '관', '실', '센터']):
        return 'club_room'
    
    return 'other'


def extract_professor_name(name: str) -> str:
    """
    교수님 이름 추출
    """
    if '교수' in name:
        # "조진성교수연구실" -> "조진성"
        match = re.search(r'([가-힣]+)교수', name)
        if match:
            return match.group(1)
    return ""


def is_accessible(room_type: str) -> bool:
    """
    일반 학생 접근 가능 여부
    """
    accessible_types = ['classroom', 'seminar_room', 'amenity', 'restroom', 'student_council']
    return room_type in accessible_types


def extract_keywords(name: str, room_type: str) -> List[str]:
    """
    검색용 키워드 추출
    """
    keywords = []
    
    # 기본 키워드
    keywords.append(name)
    
    # 교수님 이름
    prof_name = extract_professor_name(name)
    if prof_name:
        keywords.append(prof_name)
        keywords.append(f"{prof_name}교수")
    
    # 공간 유형별 키워드
    if room_type == 'classroom':
        keywords.extend(['강의실', '수업'])
    elif room_type == 'lab':
        keywords.extend(['연구실', '실험실', 'lab'])
    elif room_type == 'amenity':
        if '매점' in name:
            keywords.extend(['매점', '편의점', '밥', '간식', '음료'])
        if '휴게실' in name:
            keywords.extend(['휴게실', '쉬는곳'])
    elif room_type == 'student_council':
        keywords.extend(['학생회', '학생회실'])
    elif room_type == 'restroom':
        keywords.extend(['화장실', '휴게실'])
    
    return list(set(keywords))  # 중복 제거


def parse_all_rooms() -> List[Dict]:
    """
    모든 공간 데이터 파싱
    """
    # 층별로 분리 (빈 줄로 구분)
    sections = [s.strip() for s in RAW_DATA.strip().split('\n\n') if s.strip()]
    
    all_rooms = []
    
    for section in sections:
        floor, rooms = parse_floor(section)
        
        for room in rooms:
            room_type = classify_room_type(room['name'])
            prof_name = extract_professor_name(room['name'])
            keywords = extract_keywords(room['name'], room_type)
            
            all_rooms.append({
                'code': room['code'],
                'name': room['name'],
                'floor': floor,
                'room_type': room_type,
                'professor_name': prof_name,
                'is_accessible': is_accessible(room_type),
                'keywords': ','.join(keywords)
            })
    
    return all_rooms


if __name__ == "__main__":
    rooms = parse_all_rooms()
    
    print(f"총 {len(rooms)}개 공간 파싱 완료\n")
    
    # 유형별 통계
    type_counts = {}
    for room in rooms:
        room_type = room['room_type']
        type_counts[room_type] = type_counts.get(room_type, 0) + 1
    
    print("=== 공간 유형별 통계 ===")
    for room_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{room_type}: {count}개")
    
    print("\n=== 샘플 데이터 (각 유형별 1개) ===")
    shown_types = set()
    for room in rooms:
        if room['room_type'] not in shown_types:
            print(f"\n{room['room_type']}:")
            print(f"  코드: {room['code']}")
            print(f"  이름: {room['name']}")
            print(f"  층: {room['floor']}")
            print(f"  교수: {room['professor_name']}")
            print(f"  접근가능: {room['is_accessible']}")
            print(f"  키워드: {room['keywords'][:100]}...")
            shown_types.add(room['room_type'])