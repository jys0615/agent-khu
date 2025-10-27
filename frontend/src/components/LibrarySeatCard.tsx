import React from 'react';

interface LibrarySeatCardProps {
    seat: {
        location: string;
        floor: string | null;
        total: number;
        available: number;
        usage_rate: number;
    };
}

const LibrarySeatCard: React.FC<LibrarySeatCardProps> = ({ seat }) => {
    // 혼잡도에 따른 색상
    const getStatusColor = (rate: number) => {
        if (rate < 50) return 'bg-green-100 text-green-700 border-green-300';
        if (rate < 80) return 'bg-yellow-100 text-yellow-700 border-yellow-300';
        return 'bg-red-100 text-red-700 border-red-300';
    };

    const getStatusText = (rate: number) => {
        if (rate < 50) return '🟢 여유';
        if (rate < 80) return '🟡 보통';
        return '🔴 혼잡';
    };

    return (
        <div className={`p-4 rounded-lg border-2 ${getStatusColor(seat.usage_rate)}`}>
            {/* 상단: 위치 */}
            <div className="flex items-center justify-between mb-2">
                <div>
                    <h4 className="text-base font-bold">{seat.location}</h4>
                    {seat.floor && (
                        <p className="text-xs text-gray-600 mt-1">{seat.floor}</p>
                    )}
                </div>
                <span className="text-sm font-bold">{getStatusText(seat.usage_rate)}</span>
            </div>

            {/* 중간: 좌석 현황 */}
            <div className="my-3">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-700">이용 가능</span>
                    <span className="text-2xl font-bold text-blue-600">
                        {seat.available}
                    </span>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">총 좌석</span>
                    <span className="text-sm text-gray-600">{seat.total}석</span>
                </div>
            </div>

            {/* 하단: 진행바 */}
            <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                    className="h-2 rounded-full transition-all duration-300"
                    style={{
                        width: `${seat.usage_rate}%`,
                        backgroundColor: seat.usage_rate < 50 ? '#10b981' : seat.usage_rate < 80 ? '#f59e0b' : '#ef4444'
                    }}
                />
            </div>
            <p className="text-xs text-gray-500 text-right mt-1">
                사용률 {seat.usage_rate}%
            </p>
        </div>
    );
};

export default LibrarySeatCard;