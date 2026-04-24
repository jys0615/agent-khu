import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as authApi from '../api/auth';
import MagnoliaLogo from '../components/MagnoliaLogo';

const FEATURES = [
    { icon: '🏛', label: '강의실 위치 & 길찾기' },
    { icon: '🍽', label: '오늘의 학식 메뉴' },
    { icon: '📚', label: '도서관 좌석 조회' },
    { icon: '🎓', label: '졸업요건 & 교과과정' },
    { icon: '📢', label: '학사 공지사항' },
    { icon: '🚌', label: '셔틀버스 시간표' },
];

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [formData, setFormData] = useState({ student_id: '', password: '' });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const response = await authApi.login(formData);
            login(response.access_token, response.user);
            navigate('/');
        } catch (err: any) {
            setError(err.message || '로그인에 실패했습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">

            {/* ── 왼쪽 브랜딩 패널 (lg+) ─────────────────────────── */}
            <div className="hidden lg:flex lg:w-[52%] relative flex-col items-center justify-center p-12 overflow-hidden"
                 style={{ background: 'linear-gradient(145deg, #6B1030 0%, #8B1538 40%, #A52050 100%)' }}>

                {/* 배경 장식 원들 */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute -top-20 -left-20 w-80 h-80 rounded-full"
                         style={{ background: 'radial-gradient(circle, rgba(197,160,74,0.12) 0%, transparent 70%)' }}/>
                    <div className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full"
                         style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%)' }}/>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full border"
                         style={{ borderColor: 'rgba(255,255,255,0.04)' }}/>
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[340px] h-[340px] rounded-full border"
                         style={{ borderColor: 'rgba(197,160,74,0.08)' }}/>
                </div>

                {/* 콘텐츠 */}
                <div className="relative z-10 text-center max-w-sm">
                    <MagnoliaLogo size={88} className="mx-auto mb-6 drop-shadow-lg" />
                    <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">Agent KHU</h1>
                    <p className="text-white/70 text-base mb-3">경희대학교 AI 캠퍼스 어시스턴트</p>
                    <p className="text-white/40 text-xs mb-10 font-light tracking-wide uppercase">
                        Powered by Claude Sonnet 4 · MCP
                    </p>

                    <div className="grid grid-cols-2 gap-3 text-left">
                        {FEATURES.map((f) => (
                            <div key={f.label}
                                 className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                                 style={{ background: 'rgba(255,255,255,0.07)', backdropFilter: 'blur(4px)' }}>
                                <span className="text-xl">{f.icon}</span>
                                <span className="text-white/80 text-xs font-medium leading-tight">{f.label}</span>
                            </div>
                        ))}
                    </div>

                    <p className="mt-10 text-white/30 text-xs">경희대학교 소프트웨어융합대학</p>
                </div>
            </div>

            {/* ── 오른쪽 폼 패널 ──────────────────────────────────── */}
            <div className="w-full lg:w-[48%] flex items-center justify-center p-6 bg-khu-warm">
                <div className="w-full max-w-[360px]">

                    {/* 모바일 로고 */}
                    <div className="lg:hidden text-center mb-8">
                        <MagnoliaLogo size={64} className="mx-auto mb-3" />
                        <h1 className="text-2xl font-bold text-khu-primary">Agent KHU</h1>
                        <p className="text-gray-500 text-sm mt-1">경희대학교 AI 캠퍼스 어시스턴트</p>
                    </div>

                    {/* 폼 카드 */}
                    <div className="bg-white rounded-2xl shadow-glass p-8 border border-gray-100">
                        <h2 className="text-xl font-bold text-gray-900 mb-0.5">로그인</h2>
                        <p className="text-sm text-gray-400 mb-6">학번과 비밀번호를 입력하세요</p>

                        {error && (
                            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-xl
                                            text-red-700 text-sm flex items-center gap-2">
                                <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd"
                                          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                                          clipRule="evenodd"/>
                                </svg>
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1.5">학번</label>
                                <input
                                    type="text"
                                    name="username"
                                    value={formData.student_id}
                                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                                    className="input-chat"
                                    placeholder="2021123456"
                                    required
                                    autoComplete="username"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1.5">비밀번호</label>
                                <input
                                    type="password"
                                    name="current-password"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="input-chat"
                                    placeholder="비밀번호를 입력하세요"
                                    required
                                    autoComplete="current-password"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-base"
                            >
                                {isLoading ? (
                                    <>
                                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10"
                                                    stroke="currentColor" strokeWidth="4"/>
                                            <path className="opacity-75" fill="currentColor"
                                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                        </svg>
                                        로그인 중...
                                    </>
                                ) : '로그인'}
                            </button>
                        </form>

                        <div className="mt-6 pt-5 border-t border-gray-100 text-center">
                            <p className="text-sm text-gray-500">
                                계정이 없으신가요?{' '}
                                <button
                                    onClick={() => navigate('/register')}
                                    className="text-khu-primary font-semibold hover:underline"
                                >
                                    회원가입
                                </button>
                            </p>
                        </div>
                    </div>

                    <p className="text-center mt-5 text-xs text-gray-400">
                        경희대학교 소프트웨어융합대학
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
