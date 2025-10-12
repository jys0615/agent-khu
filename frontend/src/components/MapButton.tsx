import React from 'react';

interface MapButtonProps {
    mapLink: string;
}

const MapButton: React.FC<MapButtonProps> = ({ mapLink }) => {
    const handleMapClick = () => {
        // 네이버 지도 URL을 새 탭에서 열기
        window.open(mapLink, '_blank');
    };

    return (
        <div className="flex justify-start mt-2 ml-10">
            <button
                onClick={handleMapClick}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors shadow-md"
            >
                <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 013.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                    />
                </svg>
                <span>네이버 지도로 길찾기</span>
            </button>
        </div>
    );
};

export default MapButton;