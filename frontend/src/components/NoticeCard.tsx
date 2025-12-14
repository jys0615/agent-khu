import React from 'react';

interface NoticeCardProps {
    notice: {
        title: string;
        date: string;
        url: string;
        source?: string;
        author?: string;
        views?: number;
    };
}

const NoticeCard: React.FC<NoticeCardProps> = ({ notice }) => {
    // 소스별 라벨 (경희대 컬러)
    const sourceLabels: { [key: string]: { label: string; color: string; icon: string } } = {
        swedu: {
            label: 'SW중심대학',
            color: 'bg-khu-red-50 text-khu-primary border-khu-red-100',
            icon: '💻'
        },
        department: {
            label: '컴퓨터공학부',
            color: 'bg-blue-50 text-khu-accent border-blue-100',
            icon: '🎓'
        },
        schedule: {
            label: '학사일정',
            color: 'bg-purple-50 text-purple-700 border-purple-100',
            icon: '📅'
        },
        student: {
            label: '학생회',
            color: 'bg-green-50 text-green-700 border-green-100',
            icon: '👥'
        },
        library: {
            label: '도서관',
            color: 'bg-yellow-50 text-yellow-700 border-yellow-100',
            icon: '📚'
        }
    };

    const sourceInfo = sourceLabels[notice.source || 'swedu'] || sourceLabels['swedu'];

    // 날짜 포맷팅
    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            const now = new Date();
            const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

            if (diffDays === 0) return '오늘';
            if (diffDays === 1) return '어제';
            if (diffDays < 7) return `${diffDays}일 전`;
            return dateStr;
        } catch {
            return dateStr;
        }
    };

    // NEW 뱃지 (7일 이내)
    const isNew = () => {
        try {
            const date = new Date(notice.date);
            const now = new Date();
            const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
            return diffDays <= 7;
        } catch {
            return false;
        }
    };

    return (
        <a
            href={notice.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block card hover:border-khu-primary/30 group relative overflow-hidden"
        >
            {/* NEW 뱃지 */}
            {isNew() && (
                <div className="absolute top-3 right-3">
                    <span className="bg-khu-primary text-white text-xs font-bold px-2 py-1 rounded-full animate-pulse-slow">
                        NEW
                    </span>
                </div>
            )}

            {/* 상단: 소스 라벨 */}
            <div className="flex items-center gap-2 mb-3">
                <span className={`text-xs px-3 py-1 rounded-full border font-medium ${sourceInfo.color}`}>
                    <span className="mr-1">{sourceInfo.icon}</span>
                    {sourceInfo.label}
                </span>
                {notice.views !== undefined && notice.views > 0 && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                        </svg>
                        {notice.views.toLocaleString()}
                    </span>
                )}
            </div>

            {/* 제목 */}
            <h4 className="text-sm font-bold text-gray-900 group-hover:text-khu-primary transition-colors line-clamp-2 mb-3 min-h-[2.5rem]">
                {notice.title}
            </h4>

            {/* 하단: 날짜 & 작성자 */}
            <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                    </svg>
                    <span>{formatDate(notice.date)}</span>
                </div>
                {notice.author && (
                    <div className="flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                        <span className="max-w-[100px] truncate">{notice.author}</span>
                    </div>
                )}
            </div>

            {/* 호버 시 "보기" 표시 */}
            <div className="mt-3 pt-3 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-y-1 group-hover:translate-y-0">
                <div className="flex items-center justify-between text-xs font-medium text-khu-primary">
                    <span>자세히 보기</span>
                    <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                </div>
            </div>
        </a>
    );
};

export default NoticeCard;