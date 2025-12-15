import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface RequirementGroup {
    key: string;
    name: string;
    min_credits: number;
    description: string;
    completed_credits?: number;
}

interface SpecialRequirements {
    english_courses_required: number;
    english_courses_transfer?: number;
    graduation_project_required: boolean;
    sw_education_required: boolean;
    sw_education_credits: number;
}

interface GraduationEvaluation {
    admission_year: number;
    department: string;
    completed_credits: number;
    total_credits_required: number;
    major_credits_required: number;
    remaining_credits: number;
    progress_percent: number;
    groups: RequirementGroup[];
    special_requirements: SpecialRequirements;
    status: 'on_track' | 'needs_attention' | 'completed';
}

interface GraduationProgressProps {
    admissionYear?: number;
    department?: string;
}

const GraduationProgress: React.FC<GraduationProgressProps> = ({ 
    admissionYear = 2019,
    department = '컴퓨터공학과' 
}) => {
    const { token } = useAuth();
    const [evaluation, setEvaluation] = useState<GraduationEvaluation | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchEvaluation = async () => {
            if (!token) return;

            try {
                setLoading(true);
                const response = await fetch(
                    `http://localhost:8000/api/curriculum/evaluation?admission_year=${admissionYear}&department=${encodeURIComponent(department)}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                setEvaluation(data);
                setError('');
            } catch (err: any) {
                console.error('졸업요건 조회 실패:', err);
                setError('졸업요건 정보를 불러올 수 없습니다.');
            } finally {
                setLoading(false);
            }
        };

        fetchEvaluation();
    }, [token, admissionYear, department]);

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">🎓 졸업 진행도</h3>
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded"></div>
                    <div className="h-32 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (error || !evaluation) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">🎓 졸업 진행도</h3>
                <p className="text-gray-600">{error || '졸업요건 정보를 찾을 수 없습니다.'}</p>
            </div>
        );
    }

    const progressColor = 
        evaluation.progress_percent === 100 ? 'bg-green-500' :
        evaluation.progress_percent >= 75 ? 'bg-blue-500' :
        evaluation.progress_percent >= 50 ? 'bg-yellow-500' :
        'bg-orange-500';

    const statusText = 
        evaluation.status === 'completed' ? '✅ 졸업 완료' :
        evaluation.status === 'on_track' ? '🎯 순조로운 진행 중' :
        '⚠️ 주의 필요';

    const statusColor =
        evaluation.status === 'completed' ? 'text-green-600' :
        evaluation.status === 'on_track' ? 'text-blue-600' :
        'text-red-600';

    return (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">🎓 졸업 진행도</h3>
                <p className="text-sm text-gray-600">{evaluation.admission_year}학년도 {evaluation.department}</p>
            </div>

            {/* 진행도 바 */}
            <div className="space-y-2">
                <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">전체 학점</span>
                    <span className="text-sm font-semibold text-gray-800">
                        {evaluation.completed_credits} / {evaluation.total_credits_required} 학점
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                        className={`h-full ${progressColor} transition-all duration-300`}
                        style={{ width: `${Math.min(evaluation.progress_percent, 100)}%` }}
                    ></div>
                </div>
                <p className={`text-sm font-semibold ${statusColor}`}>
                    {statusText} ({evaluation.progress_percent.toFixed(1)}%)
                </p>
            </div>

            {/* 주요 정보 */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                    <p className="text-xs text-blue-600 font-medium">필수 학점</p>
                    <p className="text-2xl font-bold text-blue-800">{evaluation.major_credits_required}</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                    <p className="text-xs text-green-600 font-medium">남은 학점</p>
                    <p className="text-2xl font-bold text-green-800">{Math.max(0, evaluation.remaining_credits)}</p>
                </div>
            </div>

            {/* 학점 그룹별 진행도 */}
            <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-800">📚 이수 과목 현황</h4>
                <div className="space-y-2">
                    {evaluation.groups.map((group) => (
                        <div key={group.key} className="space-y-1">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-700 font-medium">{group.name}</span>
                                <span className="text-gray-600">
                                    {group.completed_credits ?? 0} / {group.min_credits} 학점
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                                    style={{
                                        width: `${Math.min(
                                            ((group.completed_credits ?? 0) / group.min_credits) * 100,
                                            100
                                        )}%`
                                    }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 특수 요구사항 */}
            <div className="space-y-2">
                <h4 className="text-sm font-semibold text-gray-800">⭐ 특수 요구사항</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-700">영어 강의 이수</span>
                        <span className="text-gray-600">{evaluation.special_requirements.english_courses_required}과목</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-gray-700">졸업 프로젝트</span>
                        <span className={evaluation.special_requirements.graduation_project_required ? 'text-blue-600 font-medium' : 'text-gray-600'}>
                            {evaluation.special_requirements.graduation_project_required ? '✓ 필수' : '선택'}
                        </span>
                    </div>
                    {evaluation.special_requirements.sw_education_required && (
                        <div className="flex items-center justify-between">
                            <span className="text-gray-700">SW교육</span>
                            <span className="text-gray-600">{evaluation.special_requirements.sw_education_credits}학점</span>
                        </div>
                    )}
                </div>
            </div>

            {/* 동기화 정보 */}
            <div className="text-xs text-gray-500 text-center border-t pt-4">
                매주 일요일 자동 동기화 됩니다
            </div>
        </div>
    );
};

export default GraduationProgress;
