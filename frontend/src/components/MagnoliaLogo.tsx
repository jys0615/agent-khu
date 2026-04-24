import React from 'react';

interface MagnoliaLogoProps {
    size?: number;
    className?: string;
}

const MagnoliaLogo: React.FC<MagnoliaLogoProps> = ({ size = 40, className = '' }) => (
    <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="경희대학교 AI 어시스턴트 로고"
    >
        {/* 배경 원 */}
        <circle cx="32" cy="32" r="30" fill="#8B1538" />
        {/* 내원 골드 테두리 */}
        <circle cx="32" cy="32" r="27" fill="none" stroke="#C5A04A" strokeWidth="0.7" opacity="0.5" />

        {/* 목련 꽃잎 4방향 (메인) */}
        <path d="M32 5 C27 14 24 22 32 32 C40 22 37 14 32 5Z"      fill="white" opacity="0.93"/>
        <path d="M59 32 C50 27 42 24 32 32 C42 40 50 37 59 32Z"    fill="white" opacity="0.93"/>
        <path d="M32 59 C37 50 40 42 32 32 C24 42 27 50 32 59Z"    fill="white" opacity="0.93"/>
        <path d="M5 32 C14 37 22 40 32 32 C22 24 14 27 5 32Z"      fill="white" opacity="0.93"/>

        {/* 목련 꽃잎 4방향 (대각선, 작은) */}
        <path d="M54 10 C46 19 40 26 32 32 C38 23 44 17 54 10Z"    fill="white" opacity="0.62"/>
        <path d="M54 54 C46 45 40 38 32 32 C38 41 44 47 54 54Z"    fill="white" opacity="0.62"/>
        <path d="M10 54 C18 45 24 38 32 32 C26 41 20 47 10 54Z"    fill="white" opacity="0.62"/>
        <path d="M10 10 C18 19 24 26 32 32 C26 23 20 17 10 10Z"    fill="white" opacity="0.62"/>

        {/* 꽃심 */}
        <circle cx="32" cy="32" r="5.5" fill="#C5A04A"/>
        <circle cx="32" cy="32" r="3"   fill="#8B1538"/>
        <circle cx="32" cy="32" r="1.5" fill="#C5A04A" opacity="0.8"/>
    </svg>
);

export default MagnoliaLogo;
