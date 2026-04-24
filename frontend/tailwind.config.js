/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                khu: {
                    primary:   '#8B1538',   // 경희 크림슨
                    dark:      '#6B1030',   // 짙은 크림슨
                    light:     '#B5396B',   // 밝은 크림슨
                    gold:      '#C5A04A',   // 경희 골드
                    'gold-lt': '#F0E4C4',   // 연한 골드 배경
                    navy:      '#1B2A4A',   // 딥 네이비
                    warm:      '#F7F4F0',   // 따뜻한 배경
                    // 기존 호환
                    secondary: '#C5A04A',
                    accent:    '#1B2A4A',
                    50:  '#FFF1F4',
                    100: '#FFE1E8',
                    200: '#FFC0D0',
                    500: '#8B1538',
                    600: '#721129',
                    700: '#5A0D20',
                    red: {
                        50:  '#FFF1F4',
                        100: '#FFE1E8',
                        500: '#8B1538',
                        600: '#721129',
                        700: '#5A0D20',
                    },
                },
            },
            fontFamily: {
                sans: ['Pretendard', 'Noto Sans KR', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            },
            spacing: {
                '18': '4.5rem',
                '88': '22rem',
            },
            borderRadius: {
                'bubble':    '20px',
                'bubble-sm': '14px',
                '2.5xl':     '20px',
            },
            boxShadow: {
                'card':       '0 1px 4px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.05)',
                'card-hover': '0 8px 24px rgba(139,21,56,0.12)',
                'glass':      '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
                'chat-in':    '0 2px 8px rgba(0,0,0,0.06)',
            },
            animation: {
                'slide-up':     'slideUp 0.22s ease-out',
                'slide-in':     'slideIn 0.2s ease-out',
                'fade-in':      'fadeIn 0.18s ease-out',
                'cursor-blink': 'cursorBlink 1.1s step-end infinite',
                'tool-enter':   'toolEnter 0.25s ease-out',
                'typing':       'typing 1.5s infinite',
            },
            keyframes: {
                slideUp: {
                    '0%':   { transform: 'translateY(14px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)',    opacity: '1' },
                },
                slideIn: {
                    '0%':   { transform: 'translateX(-8px)', opacity: '0' },
                    '100%': { transform: 'translateX(0)',     opacity: '1' },
                },
                fadeIn: {
                    '0%':   { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                cursorBlink: {
                    '0%, 100%': { opacity: '1' },
                    '50%':      { opacity: '0' },
                },
                toolEnter: {
                    '0%':   { transform: 'translateY(-4px) scale(0.96)', opacity: '0' },
                    '100%': { transform: 'translateY(0) scale(1)',        opacity: '1' },
                },
                typing: {
                    '0%, 100%': { opacity: '0.4' },
                    '50%':      { opacity: '1' },
                },
            },
        },
    },
    plugins: [],
};
