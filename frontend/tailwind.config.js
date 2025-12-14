/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // 경희대 공식 컬러
                khu: {
                    primary: '#8B1538',    // 경희 빨강
                    secondary: '#C5A572',  // 골드
                    accent: '#003A70',     // 파랑
                    red: {
                        50: '#FFF1F2',
                        100: '#FFE1E6',
                        500: '#8B1538',
                        600: '#721129',
                        700: '#5A0D20',
                    }
                },
                // 채팅 UI 컬러
                chat: {
                    user: '#E8F4FD',       // 사용자 메시지 배경
                    bot: '#FFFFFF',        // 봇 메시지 배경
                    userText: '#003A70',   // 사용자 텍스트
                    botText: '#212529',    // 봇 텍스트
                }
            },
            fontFamily: {
                sans: ['Noto Sans KR', 'Pretendard', '-apple-system', 'sans-serif'],
            },
            spacing: {
                '18': '4.5rem',
                '88': '22rem',
            },
            borderRadius: {
                'bubble': '18px',
            },
            boxShadow: {
                'card': '0 1px 3px rgba(0, 0, 0, 0.1)',
                'card-hover': '0 4px 12px rgba(139, 21, 56, 0.15)',
            },
            animation: {
                'slide-up': 'slideUp 0.3s ease-out',
                'fade-in': 'fadeIn 0.3s ease-out',
                'typing': 'typing 1.5s infinite',
            },
            keyframes: {
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                typing: {
                    '0%, 100%': { opacity: '0.4' },
                    '50%': { opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}