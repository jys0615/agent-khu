import React from 'react';

interface CourseCardProps {
    course: {
        code: string;
        name: string;
        professor: string;
        credits: number;
        time: string;
        classroom: string;
        classification: string;
    };
}

const CourseCard: React.FC<CourseCardProps> = ({ course }) => {
    // 이수 구분 색상
    const getClassificationColor = (classification: string) => {
        if (classification.includes('필수')) return 'bg-red-100 text-red-700';
        if (classification.includes('선택')) return 'bg-blue-100 text-blue-700';
        return 'bg-gray-100 text-gray-700';
    };

    return (
        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            {/* 상단: 과목명 + 학점 */}
            <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                    <h4 className="text-base font-bold text-gray-800 mb-1">
                        {course.name}
                    </h4>
                    <p className="text-xs text-gray-500">{course.code}</p>
                </div>
                <span className="text-lg font-bold text-blue-600 ml-2">
                    {course.credits}학점
                </span>
            </div>

            {/* 이수 구분 */}
            <div className="mb-3">
                <span className={`text-xs px-2 py-1 rounded ${getClassificationColor(course.classification)}`}>
                    {course.classification}
                </span>
            </div>

            {/* 교수 */}
            <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-gray-600">👨‍🏫 {course.professor}</span>
            </div>

            {/* 시간/강의실 */}
            <div className="pt-2 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">⏰ {course.time}</span>
                    <span className="text-gray-600">📍 {course.classroom}</span>
                </div>
            </div>
        </div>
    );
};

export default CourseCard;