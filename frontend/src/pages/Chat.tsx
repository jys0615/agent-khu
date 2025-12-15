import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ChatInterface from '../components/ChatInterface';

const Chat: React.FC = () => {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [showDropdown, setShowDropdown] = React.useState(false);
    const [theme, setTheme] = React.useState<'light' | 'dark'>(() => {
        const saved = localStorage.getItem('theme');
        return (saved === 'dark' || saved === 'light') ? (saved as 'light' | 'dark') : 'light';
    });

    // 테마 적용
    React.useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className={theme === 'dark' ? 'min-h-screen bg-slate-900' : 'min-h-screen bg-gradient-to-br from-gray-50 via-white to-khu-red-50'}>
            {/* 헤더 */}
            <header className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center justify-between">
                        {/* 로고 및 타이틀 */}
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-md">
                                KHU
                            </div>
                            <div>
                                <h1 className="text-lg sm:text-xl font-bold text-khu-primary">Agent KHU</h1>
                                <p className="text-xs text-gray-600">경희대학교 AI 캠퍼스 어시스턴트</p>
                            </div>
                        </div>

                        {/* 사용자 메뉴 */}
                        <div className="relative">
                            <button
                                onClick={() => setShowDropdown(!showDropdown)}
                                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                            >
                                <div className="w-8 h-8 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-full flex items-center justify-center text-white font-bold text-xs">
                                    {user?.admission_year ? String(user.admission_year).slice(-2) : user?.student_id.slice(0, 2)}
                                </div>
                                <span className="hidden sm:block text-sm font-medium text-gray-700">
                                    {user?.name || user?.student_id}
                                </span>
                                <svg className={`w-4 h-4 text-gray-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>

                            {/* 드롭다운 */}
                            {showDropdown && (
                                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-2 animate-fade-in">
                                    <button
                                        onClick={() => {
                                            navigate('/profile');
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                                        </svg>
                                        내 정보
                                    </button>
                                    <button
                                        onClick={() => {
                                            toggleTheme();
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                                    >
                                        {theme === 'light' ? (
                                            <>
                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                                                </svg>
                                                다크 모드
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                                                </svg>
                                                라이트 모드
                                            </>
                                        )}
                                    </button>
                                    <div className="border-t border-gray-100 my-1"></div>
                                    <button
                                        onClick={() => {
                                            handleLogout();
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" />
                                        </svg>
                                        로그아웃
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* 메인 채팅 */}
            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
                <ChatInterface />
            </main>

            {/* 푸터 */}
            <footer className="text-center py-6 text-gray-500 text-sm border-t border-gray-100 mt-8">
                <p className="mb-1">🏫 경희대학교 소프트웨어융합대학</p>
                <p className="text-xs text-gray-400">
                    국제캠퍼스 전자정보대학관 · Powered by Claude Sonnet 4
                </p>
            </footer>
        </div>
    );
};

export default Chat;
