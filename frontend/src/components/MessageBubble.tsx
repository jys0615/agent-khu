import React from 'react';
import ReactMarkdown from 'react-markdown';
import NoticeCard from './NoticeCard';
import MealCard from './MealCard';
import LibrarySeatCard from './LibrarySeatCard';
import ShuttleCard from './ShuttleCard';
import CourseCard from './CourseCard';

interface MessageBubbleProps {
    message: {
        text: string;
        isUser: boolean;
        classroomInfo?: any;
        notices?: any[];
        meals?: any[];
        seats?: any[];
        shuttle?: any;
        shuttles?: any[];
        courses?: any[];
    };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    return (
        <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`rounded-lg px-4 py-3 max-w-[70%] ${message.isUser
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                    }`}
            >
                {/* Markdown 렌더링 */}
                <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                        components={{
                            p: ({ node, ...props }) => <p className="whitespace-pre-wrap mb-2" {...props} />,
                            strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
                            a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" {...props} />
                        }}
                    >
                        {message.text}
                    </ReactMarkdown>
                </div>

                {/* 강의실 정보 */}
                {message.classroomInfo && (
                    <div className="mt-3 p-3 bg-white rounded-lg shadow-sm">
                        <p className="text-sm font-semibold text-gray-800">
                            📍 {message.classroomInfo.code} - {message.classroomInfo.room_name}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                            {message.classroomInfo.floor}층 · {message.classroomInfo.building_name}
                        </p>
                    </div>
                )}

                {/* 공지사항 */}
                {message.notices && message.notices.length > 0 && (
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-700">📢 공지사항</span>
                            <span className="text-xs text-gray-500">({message.notices.length}개)</span>
                        </div>
                        {message.notices.map((notice, idx) => (
                            <NoticeCard key={idx} notice={notice} />
                        ))}
                    </div>
                )}

                {/* 학식 메뉴 */}
                {message.meals && message.meals.length > 0 && (
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-700">🍚 학식 메뉴</span>
                            <span className="text-xs text-gray-500">({message.meals.length}개)</span>
                        </div>
                        {message.meals.map((meal, idx) => (
                            <MealCard key={idx} meal={meal} />
                        ))}
                    </div>
                )}

                {/* 도서관 좌석 */}
                {message.seats && message.seats.length > 0 && (
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-700">📚 도서관 좌석</span>
                            <span className="text-xs text-gray-500">({message.seats.length}개)</span>
                        </div>
                        {message.seats.map((seat, idx) => (
                            <LibrarySeatCard key={idx} seat={seat} />
                        ))}
                    </div>
                )}

                {/* 셔틀버스 (다음 버스) */}
                {message.shuttle && (
                    <div className="mt-4">
                        <div className="mb-3">
                            <span className="text-sm font-bold text-gray-700">🚌 다음 버스</span>
                        </div>
                        <ShuttleCard shuttle={message.shuttle} />
                    </div>
                )}

                {/* 셔틀버스 (전체 시간표) */}
                {message.shuttles && message.shuttles.length > 0 && (
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-700">🚌 셔틀버스</span>
                        </div>
                        {message.shuttles.map((shuttle, idx) => (
                            <ShuttleCard key={idx} shuttle={shuttle} />
                        ))}
                    </div>
                )}

                {/* 수강신청 강좌 */}
                {message.courses && message.courses.length > 0 && (
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center gap-2 mb-3">
                            <span className="text-sm font-bold text-gray-700">📖 수강 가능 과목</span>
                            <span className="text-xs text-gray-500">({message.courses.length}개)</span>
                        </div>
                        {message.courses.map((course, idx) => (
                            <CourseCard key={idx} course={course} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageBubble;