import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ChatInterface from '../components/ChatInterface';
import MagnoliaLogo from '../components/MagnoliaLogo';

const Chat: React.FC = () => {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [showDropdown, setShowDropdown] = React.useState(false);
    const [theme, setTheme] = React.useState<'light' | 'dark'>(() => {
        const saved = localStorage.getItem('theme');
        return (saved === 'dark' || saved === 'light') ? saved : 'light';
    });

    React.useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    // 외부 클릭 시 드롭다운 닫기
    React.useEffect(() => {
        const handler = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (!target.closest('[data-dropdown]')) setShowDropdown(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');
    const handleLogout = () => { logout(); navigate('/login'); };

    const userInitial = user?.name?.charAt(0).toUpperCase() ||
                        user?.student_id?.slice(0, 2) || 'U';

    const isDark = theme === 'dark';

    return (
        <div className="flex flex-col min-h-screen" style={{ backgroundColor: isDark ? '#0f1117' : '#F7F4F0' }}>

            {/* ── Header ─────────────────────────────────────────── */}
            <header className="header-glass">
                <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between gap-3">

                    {/* 로고 */}
                    <div className="flex items-center gap-2.5 min-w-0">
                        <MagnoliaLogo size={32} />
                        <div className="flex items-baseline gap-1.5 min-w-0">
                            <span className="font-bold text-khu-primary text-[15px] whitespace-nowrap">
                                Agent KHU
                            </span>
                            <span className="hidden sm:inline text-[10px] font-medium px-1.5 py-0.5 rounded-full
                                           bg-khu-gold-lt text-khu-dark border border-khu-gold/30">
                                Beta
                            </span>
                        </div>
                    </div>

                    {/* 중앙 모델 배지 */}
                    <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                                    border bg-gray-50 border-gray-200 text-gray-500 flex-shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse"/>
                        Claude Sonnet 4 · MCP
                    </div>

                    {/* 우측 컨트롤 */}
                    <div className="flex items-center gap-1">

                        {/* 다크/라이트 토글 */}
                        <button
                            onClick={toggleTheme}
                            className="btn-icon"
                            title={isDark ? '라이트 모드' : '다크 모드'}
                        >
                            {isDark ? (
                                /* 태양 */
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd"
                                          d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                                          clipRule="evenodd"/>
                                </svg>
                            ) : (
                                /* 달 */
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>
                                </svg>
                            )}
                        </button>

                        {/* 유저 메뉴 */}
                        <div className="relative" data-dropdown>
                            <button
                                onClick={() => setShowDropdown(!showDropdown)}
                                className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl
                                           transition-colors hover:bg-gray-100 active:scale-[.97]"
                            >
                                <div className="w-7 h-7 rounded-full flex items-center justify-center
                                                text-white font-bold text-xs flex-shrink-0"
                                     style={{ background: 'linear-gradient(135deg, #8B1538, #6B1030)' }}>
                                    {userInitial}
                                </div>
                                <span className="hidden sm:block text-sm font-medium text-gray-700 max-w-[100px] truncate">
                                    {user?.name || user?.student_id}
                                </span>
                                <svg className={`w-3 h-3 text-gray-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`}
                                     fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd"
                                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                          clipRule="evenodd"/>
                                </svg>
                            </button>

                            {showDropdown && (
                                <div className="absolute right-0 mt-2 w-44 rounded-2xl shadow-glass border
                                                bg-white border-gray-100 py-1.5 z-50 animate-fade-in overflow-hidden">

                                    {/* 사용자 정보 */}
                                    <div className="px-4 py-2.5 border-b border-gray-100">
                                        <p className="text-xs font-semibold text-gray-800 truncate">
                                            {user?.name || '사용자'}
                                        </p>
                                        <p className="text-[11px] text-gray-400 truncate">
                                            {user?.student_id}
                                        </p>
                                    </div>

                                    <button
                                        onClick={() => { navigate('/profile'); setShowDropdown(false); }}
                                        className="w-full px-4 py-2 text-left text-sm text-gray-700
                                                   hover:bg-gray-50 flex items-center gap-2.5 transition-colors"
                                    >
                                        <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd"
                                                  d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                                                  clipRule="evenodd"/>
                                        </svg>
                                        내 정보
                                    </button>

                                    <div className="border-t border-gray-100 my-1"/>

                                    <button
                                        onClick={() => { handleLogout(); setShowDropdown(false); }}
                                        className="w-full px-4 py-2 text-left text-sm text-red-500
                                                   hover:bg-red-50 flex items-center gap-2.5 transition-colors"
                                    >
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd"
                                                  d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z"
                                                  clipRule="evenodd"/>
                                        </svg>
                                        로그아웃
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* ── Main ─────────────────────────────────────────────── */}
            <main className="flex-1 max-w-3xl mx-auto w-full px-4 pt-4 pb-2">
                <ChatInterface />
            </main>
        </div>
    );
};

export default Chat;
