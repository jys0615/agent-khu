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
    // 소스별 라벨
    const sourceLabels: { [key: string]: { label: string; color: string; icon: string } } = {
        swedu: { label: 'SW중심대학', color: 'bg-blue-100 text-blue-700', icon: '💻' },
        department: { label: '컴퓨터공학부', color: 'bg-green-100 text-green-700', icon: '🎓' },
        schedule: { label: '학사일정', color: 'bg-purple-100 text-purple-700', icon: '📅' },
    };

    const sourceInfo = sourceLabels[notice.source || 'swedu'] || sourceLabels['swedu'];

    return (
        <a
            href={notice.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all duration-200 group"
        >
            {/* 상단: 소스 라벨 */}
            <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs px-2 py-1 rounded-full ${sourceInfo.color} font-medium`}>
                    {sourceInfo.icon} {sourceInfo.label}
                </span>
                {notice.views !== undefined && notice.views > 0 && (
                    <span className="text-xs text-gray-500">👁️ {notice.views}</span>
                )}
            </div>

            {/* 제목 */}
            <h4 className="text-sm font-semibold text-gray-800 group-hover:text-blue-600 transition-colors line-clamp-2 mb-2">
                {notice.title}
            </h4>

            {/* 하단: 날짜 & 작성자 */}
            <div className="flex items-center justify-between text-xs text-gray-500">
                <span>📅 {notice.date}</span>
                {notice.author && <span>✍️ {notice.author}</span>}
            </div>

            {/* 호버 시 "보기" 표시 */}
            <div className="mt-2 text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                자세히 보기 →
            </div>
        </a>
    );
};


export default NoticeCard;