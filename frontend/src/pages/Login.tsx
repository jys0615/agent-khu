import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as authApi from '../api/auth';

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [formData, setFormData] = useState({
        student_id: '',
        password: '',
    });
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
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-khu-red-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* 로고 */}
                <div className="text-center mb-8">
                    <div className="inline-block p-4 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-2xl mb-4 shadow-lg">
                        <div className="w-16 h-16 flex items-center justify-center text-white font-bold text-2xl">
                            KHU
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold text-khu-primary mb-2">Agent KHU</h1>
                    <p className="text-gray-600">경희대학교 AI 캠퍼스 어시스턴트</p>
                </div>

                {/* 로그인 카드 */}
                <div className="bg-white rounded-2xl shadow-lg p-8">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">로그인</h2>

                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                학번
                            </label>
                            <input
                                type="text"
                                value={formData.student_id}
                                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                                className="input-chat"
                                placeholder="2021123456"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                비밀번호
                            </label>
                            <input
                                type="password"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                className="input-chat"
                                placeholder="비밀번호를 입력하세요"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn-primary w-full py-3"
                        >
                            {isLoading ? '로그인 중...' : '로그인'}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            계정이 없으신가요?{' '}
                            <button
                                onClick={() => navigate('/register')}
                                className="text-khu-primary font-medium hover:underline"
                            >
                                회원가입
                            </button>
                        </p>
                    </div>
                </div>

                <p className="text-center mt-6 text-xs text-gray-500">
                    🏫 경희대학교 소프트웨어융합대학
                </p>
            </div>
        </div>
    );
};

export default Login;
