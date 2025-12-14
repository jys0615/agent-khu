import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Profile: React.FC = () => {
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    if (!user) {
        return null;
    }

    const displayName = user.name || user.student_id;

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-khu-red-50">
            {/* 헤더 */}
            <header className="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
                    <div className="flex items-center justify-between">
                        <button
                            onClick={() => navigate('/')}
                            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
                        >
                            <div className="w-10 h-10 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-md">
                                KHU
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-khu-primary">Agent KHU</h1>
                            </div>
                        </button>
                    </div>
                </div>
            </header>

            {/* 메인 */}
            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
                <div className="bg-white rounded-2xl shadow-lg p-8">
                    {/* 프로필 헤더 */}
                    <div className="flex items-center gap-6 mb-8 pb-8 border-b border-gray-200">
                        <div className="w-20 h-20 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-lg">
                            {displayName.slice(0, 2)}
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-1">
                                {displayName}
                            </h2>
                            <p className="text-gray-600">{user.student_id}학번 · {user.department}</p>
                        </div>
                    </div>

                    {/* 정보 카드 */}
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* 학번 */}
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">학번</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.student_id}
                                </div>
                            </div>

                            {/* 입학년도 */}
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">입학년도</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.admission_year}년
                                </div>
                            </div>

                            {/* 학과 */}
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">학과</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.department}
                                </div>
                            </div>

                            {/* 캠퍼스 */}
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">캠퍼스</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.campus}
                                </div>
                            </div>

                            {/* 학년 */}
                            {user.current_grade && (
                                <div className="p-4 bg-gray-50 rounded-xl">
                                    <div className="text-sm text-gray-600 mb-1">학년</div>
                                    <div className="text-lg font-semibold text-gray-900">
                                        {user.current_grade}학년
                                    </div>
                                </div>
                            )}

                            {/* 이수학점 */}
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">이수학점</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.completed_credits} / 130학점
                                </div>
                            </div>
                        </div>

                        {/* 관심분야 */}
                        {user.interests && user.interests.length > 0 && (
                            <div className="p-4 bg-khu-red-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-2">관심분야</div>
                                <div className="flex flex-wrap gap-2">
                                    {user.interests.map((interest, idx) => (
                                        <span
                                            key={idx}
                                            className="px-3 py-1 bg-white text-khu-primary border border-khu-red-100 rounded-full text-sm font-medium"
                                        >
                                            {interest}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 액션 버튼 */}
                    <div className="mt-8 pt-8 border-t border-gray-200 flex gap-3">
                        <button
                            onClick={() => navigate('/')}
                            className="btn-secondary flex-1"
                        >
                            채팅으로 돌아가기
                        </button>
                        <button
                            onClick={handleLogout}
                            className="btn-primary bg-gray-600 hover:bg-gray-700"
                        >
                            로그아웃
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Profile;
