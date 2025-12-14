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
    // 이수 구분 색상 (경희대 컬러 적용)
    const getClassificationColor = (classification: string) => {
        if (classification.includes('필수'))
            return 'bg-khu-red-50 text-khu-primary border border-khu-red-100';
        if (classification.includes('선택'))
            return 'bg-blue-50 text-khu-accent border border-blue-100';
        if (classification.includes('교양'))
            return 'bg-khu-secondary/10 text-khu-secondary border border-khu-secondary/20';
        return 'bg-gray-50 text-gray-700 border border-gray-200';
    };

    return (
        <div className="card hover:border-khu-primary/20 group">
            {/* 상단: 과목명 + 학점 */}
            <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1 min-w-0">
                    <h4 className="text-base font-bold text-gray-900 mb-1 group-hover:text-khu-primary transition-colors line-clamp-2">
                        {course.name}
                    </h4>
                    <p className="text-xs text-gray-500 font-mono">{course.code}</p>
                </div>
                <div className="flex-shrink-0 text-center">
                    <div className="text-2xl font-bold text-khu-primary">
                        {course.credits}
                    </div>
                    <div className="text-xs text-gray-500">학점</div>
                </div>
            </div>

            {/* 이수 구분 배지 */}
            <div className="mb-3">
                <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${getClassificationColor(course.classification)}`}>
                    {course.classification}
                </span>
            </div>

            {/* 구분선 */}
            <div className="border-t border-gray-100 my-3"></div>

            {/* 교수 정보 */}
            <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                    교수
                </div>
                <span className="text-sm font-medium text-gray-700">{course.professor}</span>
            </div>

            {/* 시간/강의실 정보 */}
            <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-600">{course.time}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-600">{course.classroom}</span>
                </div>
            </div>
        </div>
    );
};

export default CourseCard;