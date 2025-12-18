import React from 'react';

interface MapButtonProps {
    mapLink?: string; // 백엔드에서 내려주는 구글맵 링크가 있으면 우선 사용
}

// 기본 목적지(폴백) — 서버에서 mapLink가 없을 때 사용
const DEST_NAME = '경희대학교 국제캠퍼스';
const DEST_LAT = 37.2439;
const DEST_LNG = 127.0785;

// Google Maps Directions 링크 생성
function buildGoogleDirectionsUrl(startLat?: number, startLng?: number) {
    const base = `https://www.google.com/maps/dir/?api=1`;
    const params = new URLSearchParams();
    // origin이 있으면 추가 (없으면 현재 위치로 간주)
    if (typeof startLat === 'number' && typeof startLng === 'number') {
        params.set('origin', `${startLat},${startLng}`);
    }
    params.set('destination', `${DEST_LAT},${DEST_LNG}`);
    // Google Maps의 경우 travelmode와 dir_action 지정 가능
    params.set('travelmode', 'transit'); // 대중교통 기본
    params.set('dir_action', 'navigate');
    return `${base}&${params.toString()}`;
}

const MapButton: React.FC<MapButtonProps> = ({ mapLink }) => {
    const handleMapClick = () => {
        // 1) 백엔드 제공 경로 링크가 있으면 우선 사용 (새 탭)
        if (mapLink) {
            window.open(mapLink, '_blank', 'noreferrer');
            return;
        }

        // 2) 없으면 클라이언트 위치 기반 Google Maps Directions
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const { latitude, longitude } = pos.coords;
                    const url = buildGoogleDirectionsUrl(latitude, longitude);
                    window.open(url, '_blank', 'noreferrer');
                },
                () => {
                    // 권한 거부/오류면 목적지만 지정해 네비게이션 열기
                    const fallbackUrl = buildGoogleDirectionsUrl();
                    window.open(fallbackUrl, '_blank', 'noreferrer');
                },
                { enableHighAccuracy: true, timeout: 8000 }
            );
        } else {
            const fallbackUrl = buildGoogleDirectionsUrl();
            window.open(fallbackUrl, '_blank', 'noreferrer');
        }
    };

    return (
        <div className="flex justify-start mt-2 ml-10">
            <button
                onClick={handleMapClick}
                className="flex items-center space-x-2 px-4 py-2 bg-[#1a73e8] text-white rounded-lg hover:bg-[#1558d6] transition-colors shadow-md"
            >
                {/* Simple "G" pin icon reminiscent of Google Maps */}
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C7.582 2 4 5.582 4 10c0 5.25 6.5 11.5 7.2 12.15a1.1 1.1 0 0 0 1.6 0C13.5 21.5 20 15.25 20 10c0-4.418-3.582-8-8-8z" fill="#34A853"/>
                    <circle cx="12" cy="10" r="4.5" fill="#fff"/>
                    <path d="M12 6c2.21 0 4 1.79 4 4h-3v2h5c.19-.64.3-1.31.3-2 0-3.314-2.686-6-6-6-2.06 0-3.875 1.034-4.95 2.61l1.64 1.27C9.59 6.44 10.71 6 12 6z" fill="#4285F4"/>
                </svg>
                <span>구글맵으로 길찾기</span>
            </button>
        </div>
    );
};

export default MapButton;