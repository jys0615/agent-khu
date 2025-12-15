import React from 'react';

interface MapButtonProps {
    mapLink?: string; // 백엔드에서 내려주는 구글맵 링크가 있으면 우선 사용
}

// 경희대학교 국제캠퍼스 전자정보대학 좌표
const DEST_NAME = '경희대학교 국제캠퍼스 전자정보대학';
const DEST_LAT = 37.245435;   // 위도
const DEST_LNG = 127.081540;  // 경도

function buildMobileRouteUrl(startLat: number, startLng: number) {
  // m.map.naver.com 딥링크 고정: 대중교통(pathType=2)
  const url =
    `https://m.map.naver.com/route.nhn?menu=route` +
    `&sname=${encodeURIComponent('현재위치')}` +
    `&sx=${startLng}&sy=${startLat}` +
    `&ename=${encodeURIComponent(DEST_NAME)}` +
    `&ex=${DEST_LNG}&ey=${DEST_LAT}` +
    `&pathType=2`; // 1: 자동차, 2: 대중교통, 3: 도보
  return url;
}

const MapButton: React.FC<MapButtonProps> = ({ mapLink }) => {
    const handleMapClick = () => {
        // 1) 백엔드 제공 경로 링크가 있으면 우선 사용 (새 탭)
        if (mapLink) {
            window.open(mapLink, '_blank', 'noreferrer');
            return;
        }

        // 2) 없으면 클라이언트 위치 기반 네이버 지도 딥링크
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const { latitude, longitude } = pos.coords;
                    const url = buildMobileRouteUrl(latitude, longitude);
                    window.location.href = url;
                },
                () => {
                    // 권한 거부/오류면 폴백: 현위치 입력 없이 목적지만 지정 (대중교통)
                    const fallbackUrl = `https://m.map.naver.com/route.nhn?menu=route&ename=${encodeURIComponent(DEST_NAME)}&ex=${DEST_LNG}&ey=${DEST_LAT}&pathType=2`;
                    window.location.href = fallbackUrl;
                },
                { enableHighAccuracy: true, timeout: 8000 }
            );
        } else {
            const fallbackUrl = `https://m.map.naver.com/route.nhn?menu=route&ename=${encodeURIComponent(DEST_NAME)}&ex=${DEST_LNG}&ey=${DEST_LAT}&pathType=2`;
            window.location.href = fallbackUrl;
        }
    };

    return (
        <div className="flex justify-start mt-2 ml-10">
            <button
                onClick={handleMapClick}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors shadow-md"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 013.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                <span>네이버 지도로 길찾기</span>
            </button>
        </div>
    );
};

export default MapButton;