import React from 'react';

interface ShuttleCardProps {
    shuttle: {
        route: string;
        departure: string;
        arrival: string;
        next_time?: string;
        note?: string;
        weekday_times?: string[];
        weekend_times?: string[];
    };
}

const ShuttleCard: React.FC<ShuttleCardProps> = ({ shuttle }) => {
    return (
        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* 상단: 노선 */}
            <div className="flex items-center justify-between mb-3">
                <h4 className="text-base font-bold text-gray-800">🚌 {shuttle.route}</h4>
                {shuttle.next_time && (
                    <span className="text-lg font-bold text-blue-600">
                        {shuttle.next_time}
                    </span>
                )}
            </div>

            {/* 중간: 출발지 → 도착지 */}
            <div className="flex items-center gap-2 mb-3">
                <span className="text-sm text-gray-700">{shuttle.departure}</span>
                <span className="text-gray-400">→</span>
                <span className="text-sm text-gray-700">{shuttle.arrival}</span>
            </div>

            {/* 시간표 (전체 조회 시) */}
            {shuttle.weekday_times && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-600 mb-2">⏰ 평일 시간표</p>
                    <div className="flex flex-wrap gap-2">
                        {shuttle.weekday_times.map((time, idx) => (
                            <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                            >
                                {time}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {shuttle.weekend_times && shuttle.weekend_times.length > 0 && (
                <div className="mt-2">
                    <p className="text-xs font-semibold text-gray-600 mb-2">⏰ 주말 시간표</p>
                    <div className="flex flex-wrap gap-2">
                        {shuttle.weekend_times.map((time, idx) => (
                            <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded"
                            >
                                {time}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* 비고 */}
            {shuttle.note && (
                <p className="text-xs text-gray-500 mt-3 pt-3 border-t border-gray-200">
                    ℹ️ {shuttle.note}
                </p>
            )}
        </div>
    );
};

export default ShuttleCard;