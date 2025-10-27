"""
유틸리티 함수들
"""
from typing import Optional
from . import schemas


def generate_naver_map_link(
    classroom: schemas.ClassroomInfo,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None
) -> str:
    """
    네이버 지도 길찾기 링크 생성
    """
    # 목적지 좌표
    dest_lat = classroom.latitude or 37.24195
    dest_lon = classroom.longitude or 127.07945
    
    # 목적지 이름
    destination_name = f"경희대학교 국제캠퍼스 전자정보대학관 {classroom.room_number}호"
    
    if user_lat and user_lon:
        # 사용자 위치가 있으면 길찾기
        return f"https://map.naver.com/p/directions/{user_lon},{user_lat},{dest_lon},{dest_lat},walk/"
    else:
        # 사용자 위치 없으면 장소 검색
        return f"https://map.naver.com/p/search/{destination_name}?c={dest_lon},{dest_lat},18,0,0,0,dh"