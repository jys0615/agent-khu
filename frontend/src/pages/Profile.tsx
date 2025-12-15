import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import * as authApi from '../api/auth';

const Profile: React.FC = () => {
    const navigate = useNavigate();
    const { user, token, login, logout } = useAuth();
    const [formValues, setFormValues] = useState({
        name: '',
        student_id: '',
        admission_year: '',
        campus: '국제캠퍼스',
        is_transfer: false,
        double_major: '',
        minor: '',
    });
    const [status, setStatus] = useState({ success: '', error: '' });
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (user) {
            setFormValues({
                name: user.name ?? '',
                student_id: user.student_id,
                admission_year: user.admission_year ? String(user.admission_year) : '',
                campus: user.campus,
                is_transfer: user.is_transfer ?? false,
                double_major: user.double_major ?? '',
                minor: user.minor ?? '',
            });
        }
    }, [user]);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const resetForm = () => {
        if (!user) return;
        setFormValues({
            name: user.name ?? '',
            student_id: user.student_id,
            admission_year: user.admission_year ? String(user.admission_year) : '',
            campus: user.campus,
            is_transfer: user.is_transfer ?? false,
            double_major: user.double_major ?? '',
            minor: user.minor ?? '',
        });
        setStatus({ success: '', error: '' });
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) {
            setStatus({ success: '', error: '인증 정보가 없습니다. 다시 로그인해주세요.' });
            return;
        }

        setIsSaving(true);
        setStatus({ success: '', error: '' });

        try {
            const admissionYearNum = formValues.admission_year ? Number(formValues.admission_year) : undefined;
            const payload: authApi.ProfileUpdateData = {
                name: formValues.name.trim() || undefined,
                student_id: formValues.student_id.trim() || undefined,
                campus: formValues.campus,
                admission_year: formValues.is_transfer ? undefined : admissionYearNum,
                is_transfer: formValues.is_transfer,
                transfer_year: formValues.is_transfer ? admissionYearNum : undefined,
                double_major: formValues.double_major.trim() || undefined,
                minor: formValues.minor.trim() || undefined,
            };

            const updatedUser = await authApi.updateProfile(token, payload);
            login(token, updatedUser);
            setStatus({ success: '프로필이 저장되었습니다.', error: '' });
        } catch (err: any) {
            setStatus({ success: '', error: err.message || '프로필 수정에 실패했습니다.' });
        } finally {
            setIsSaving(false);
        }
    };

    if (!user) {
        return null;
    }

    const displayName = user.name || user.student_id;
    const completedCredits = user.completed_credits ?? 0;
    const interests = user.interests ?? [];

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
                            {String(user.admission_year).slice(-2)}
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-1">
                                {displayName}
                            </h2>
                            <p className="text-gray-600">{String(user.admission_year).slice(-2)}학번 · {user.department}</p>
                        </div>
                    </div>

                    {/* 정보 카드 */}
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">학번</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.student_id}
                                </div>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">입학년도</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.admission_year}년
                                </div>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">학과</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.department}
                                </div>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">캠퍼스</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.campus}
                                </div>
                            </div>

                            {user.is_transfer && (
                                <div className="p-4 bg-gray-50 rounded-xl">
                                    <div className="text-sm text-gray-600 mb-1">편입년도</div>
                                    <div className="text-lg font-semibold text-gray-900">
                                        {user.transfer_year}년
                                    </div>
                                </div>
                            )}

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">복수전공</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.double_major || '미등록'}
                                </div>
                            </div>

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">다전공 / 부전공</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {user.minor || '미등록'}
                                </div>
                            </div>

                            {user.current_grade && (
                                <div className="p-4 bg-gray-50 rounded-xl">
                                    <div className="text-sm text-gray-600 mb-1">학년</div>
                                    <div className="text-lg font-semibold text-gray-900">
                                        {user.current_grade}학년
                                    </div>
                                </div>
                            )}

                            <div className="p-4 bg-gray-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-1">이수학점</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {completedCredits} / 130학점
                                </div>
                            </div>
                        </div>

                        {interests.length > 0 && (
                            <div className="p-4 bg-khu-red-50 rounded-xl">
                                <div className="text-sm text-gray-600 mb-2">관심분야</div>
                                <div className="flex flex-wrap gap-2">
                                    {interests.map((interest, idx) => (
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

                    {status.error && (
                        <div className="mt-8 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {status.error}
                        </div>
                    )}
                    {status.success && (
                        <div className="mt-8 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                            {status.success}
                        </div>
                    )}

                    {/* 정보 수정 */}
                    <form onSubmit={handleSave} className="mt-8 pt-8 border-t border-gray-200 space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">정보 수정</h3>
                                <p className="text-sm text-gray-500 mt-1">이름, 학번, 입학년도, 캠퍼스, 복수전공을 수정할 수 있습니다.</p>
                            </div>
                            <button
                                type="button"
                                onClick={resetForm}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                변경 취소
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">이름</label>
                                <input
                                    className="input-chat"
                                    value={formValues.name}
                                    onChange={(e) => setFormValues({ ...formValues, name: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">학번</label>
                                <input
                                    className="input-chat"
                                    value={formValues.student_id}
                                    onChange={(e) => setFormValues({ ...formValues, student_id: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    {formValues.is_transfer ? '편입년도' : '입학년도'}
                                </label>
                                <input
                                    type="number"
                                    className="input-chat"
                                    value={formValues.admission_year}
                                    onChange={(e) => setFormValues({ ...formValues, admission_year: e.target.value })}
                                    min={2000}
                                    max={2100}
                                />
                                {formValues.is_transfer && formValues.admission_year && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        학번: {String(Number(formValues.admission_year) - 2).slice(-2)}학번으로 계산됩니다
                                    </p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">캠퍼스</label>
                                <select
                                    className="input-chat"
                                    value={formValues.campus}
                                    onChange={(e) => setFormValues({ ...formValues, campus: e.target.value })}
                                    required
                                >
                                    <option value="국제캠퍼스">국제캠퍼스</option>
                                    <option value="서울캠퍼스">서울캠퍼스</option>
                                </select>
                            </div>
                            <div className="md:col-span-2">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formValues.is_transfer}
                                        onChange={(e) => setFormValues({ ...formValues, is_transfer: e.target.checked })}
                                        className="w-4 h-4 rounded"
                                    />
                                    <span className="text-sm font-medium text-gray-700">편입생입니다</span>
                                </label>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">복수전공</label>
                                <input
                                    className="input-chat"
                                    value={formValues.double_major}
                                    onChange={(e) => setFormValues({ ...formValues, double_major: e.target.value })}
                                    placeholder="예: 경영학과"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">다전공 / 부전공</label>
                                <input
                                    className="input-chat"
                                    value={formValues.minor}
                                    onChange={(e) => setFormValues({ ...formValues, minor: e.target.value })}
                                    placeholder="예: 데이터과학"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={resetForm}
                                className="btn-secondary flex-1"
                                disabled={isSaving}
                            >
                                원래대로
                            </button>
                            <button
                                type="submit"
                                className="btn-primary flex-1"
                                disabled={isSaving}
                            >
                                {isSaving ? '저장 중...' : '변경사항 저장'}
                            </button>
                        </div>
                    </form>

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
