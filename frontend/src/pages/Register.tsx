import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as authApi from '../api/auth';

const Register: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [formData, setFormData] = useState({
        student_id: '',
        password: '',
        email: '',
        name: '',
        department: '컴퓨터공학부',
        campus: '국제캠퍼스',
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await authApi.register(formData);
            login(response.access_token, response.user);
            navigate('/');
        } catch (err: any) {
            setError(err.message || '회원가입에 실패했습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-khu-red-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-6">
                    <h1 className="text-2xl font-bold text-khu-primary">회원가입</h1>
                    <p className="text-gray-600 mt-2">Agent KHU에 오신 것을 환영합니다</p>
                    <p className="text-sm text-gray-500 mt-1">아이디와 비밀번호는 경희대학교 인포와 동일하게 사용해주세요.</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-8">
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                학번 *
                            </label>
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                이름 *
                            </label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                className="input-chat"
                                placeholder="홍길동"
                                required
                                autoComplete="name"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                이메일 *
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                className="input-chat"
                                placeholder="example@khu.ac.kr"
                                required
                                autoComplete="email"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                비밀번호 *
                            </label>
                            <input
                                type="password"
                                name="new-password"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                className="input-chat"
                                placeholder="8자 이상 입력"
                                required
                                minLength={8}
                                autoComplete="new-password"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                학과 *
                            </label>
                            <select
                                value={formData.department}
                                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                                className="input-chat"
                                required
                            >
                                <option value="컴퓨터공학부">컴퓨터공학부</option>
                                <option value="소프트웨어융합학과">소프트웨어융합학과</option>
                                <option value="전자공학과">전자공학과</option>
                                <option value="정보디스플레이학과">정보디스플레이학과</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                캠퍼스 *
                            </label>
                            <select
                                value={formData.campus}
                                onChange={(e) => setFormData({ ...formData, campus: e.target.value })}
                                className="input-chat"
                                required
                            >
                                <option value="국제캠퍼스">국제캠퍼스</option>
                                <option value="서울캠퍼스">서울캠퍼스</option>
                            </select>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn-primary w-full py-3 mt-6"
                        >
                            {isLoading ? '가입 중...' : '회원가입'}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            이미 계정이 있으신가요?{' '}
                            <button
                                onClick={() => navigate('/login')}
                                className="text-khu-primary font-medium hover:underline"
                            >
                                로그인
                            </button>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
