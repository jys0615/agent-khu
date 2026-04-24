import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import NoticeCard from './NoticeCard';
import MealCard from './MealCard';
import LibrarySeatCard from './LibrarySeatCard';
import ShuttleCard from './ShuttleCard';
import CourseCard from './CourseCard';
import MapButton from './MapButton';

interface MessageBubbleProps {
    message: {
        text: string;
        isUser: boolean;
        isStreaming?: boolean;
        activeTools?: string[];
        classroomInfo?: any;
        notices?: any[];
        meals?: any[];
        seats?: any[];
        shuttle?: any;
        shuttles?: any[];
        courses?: any[];
        mapLink?: string;
        showMapButton?: boolean;
        timestamp?: string;
    };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
    const [showFeedback, setShowFeedback] = useState(false);

    const handleFeedback = (type: 'like' | 'dislike') => {
        setFeedback(type);
        setShowFeedback(true);

        // TODO: 백엔드에 피드백 전송
        console.log('Feedback:', type);

        // 2초 후 메시지 숨김
        setTimeout(() => setShowFeedback(false), 2000);
    };

    return (
        <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} mb-4 animate-slide-up`}>
            <div className={`flex items-start gap-2 max-w-[85%] sm:max-w-[80%]`}>
                {/* 봇 아이콘 */}
                {!message.isUser && (
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md">
                        AI
                    </div>
                )}

                <div className="flex flex-col gap-2 flex-1">
                    {/* 메시지 버블 */}
                    <div
                        className={`rounded-bubble px-5 py-3 shadow-md ${message.isUser
                                ? 'bg-khu-primary text-white ml-auto'
                                : 'bg-white text-gray-800'
                            }`}
                    >
                        {/* tool 실행 중 상태 표시 */}
                        {message.activeTools && message.activeTools.length > 0 && (
                            <div className="mb-2 space-y-1">
                                {message.activeTools.map((label, i) => (
                                    <div key={i} className="flex items-center gap-2 text-xs text-khu-primary animate-pulse">
                                        <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                        </svg>
                                        <span>{label}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* 텍스트 내용 */}
                        <div className={`prose-custom ${message.isUser ? 'prose-user text-white' : ''}`}>
                            <ReactMarkdown
                                components={{
                                    p: ({ node, ...props }) => (
                                        <p className="whitespace-pre-wrap mb-2 last:mb-0" {...props} />
                                    ),
                                    strong: ({ node, ...props }) => (
                                        <strong className={`font-bold ${message.isUser ? 'text-white' : 'text-khu-primary'}`} {...props} />
                                    ),
                                    a: ({ node, ...props }) => (
                                        <a className={`underline ${message.isUser ? 'text-white hover:text-gray-100' : 'text-khu-accent hover:text-khu-primary'}`} {...props} />
                                    ),
                                }}
                            >
                                {message.text}
                            </ReactMarkdown>
                            {/* 스트리밍 커서 */}
                            {message.isStreaming && (
                                <span className="inline-block w-0.5 h-4 bg-khu-primary ml-0.5 animate-pulse align-middle" />
                            )}
                        </div>

                        {/* 강의실 정보 */}
                        {message.classroomInfo && (
                            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                                <p className="text-sm font-semibold text-khu-primary flex items-center gap-2">
                                    📍 {message.classroomInfo.code} - {message.classroomInfo.room_name}
                                </p>
                                <p className="text-xs text-gray-600 mt-1">
                                    {message.classroomInfo.floor}층 · {message.classroomInfo.building_name}
                                </p>
                                {message.showMapButton && (
                                    <MapButton mapLink={message.mapLink} />
                                )}
                            </div>
                        )}
                    </div>

                    {/* 공지사항 */}
                    {message.notices && message.notices.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 px-2">
                                <span className="text-sm font-bold text-khu-primary">📢 공지사항</span>
                                <span className="text-xs text-gray-500">({message.notices.length}개)</span>
                            </div>
                            {message.notices.map((notice, idx) => (
                                <NoticeCard key={idx} notice={notice} />
                            ))}
                        </div>
                    )}

                    {/* 학식 메뉴 */}
                    {message.meals && message.meals.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 px-2">
                                <span className="text-sm font-bold text-khu-primary">🍚 학식 메뉴</span>
                                <span className="text-xs text-gray-500">({message.meals.length}개)</span>
                            </div>
                            {message.meals.map((meal, idx) => (
                                <MealCard key={idx} meal={meal} />
                            ))}
                        </div>
                    )}

                    {/* 도서관 좌석 */}
                    {message.seats && message.seats.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 px-2">
                                <span className="text-sm font-bold text-khu-primary">📚 도서관 좌석</span>
                                <span className="text-xs text-gray-500">({message.seats.length}개)</span>
                            </div>
                            {message.seats.map((seat, idx) => (
                                <LibrarySeatCard key={idx} seat={seat} />
                            ))}
                        </div>
                    )}

                    {/* 셔틀버스 (다음 버스) */}
                    {message.shuttle && (
                        <div>
                            <div className="px-2 mb-2">
                                <span className="text-sm font-bold text-khu-primary">🚌 다음 버스</span>
                            </div>
                            <ShuttleCard shuttle={message.shuttle} />
                        </div>
                    )}

                    {/* 셔틀버스 (전체 시간표) */}
                    {message.shuttles && message.shuttles.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 px-2">
                                <span className="text-sm font-bold text-khu-primary">🚌 셔틀버스</span>
                            </div>
                            {message.shuttles.map((shuttle, idx) => (
                                <ShuttleCard key={idx} shuttle={shuttle} />
                            ))}
                        </div>
                    )}

                    {/* 수강신청 강좌 */}
                    {message.courses && message.courses.length > 0 && (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 px-2">
                                <span className="text-sm font-bold text-khu-primary">📖 수강 가능 과목</span>
                                <span className="text-xs text-gray-500">({message.courses.length}개)</span>
                            </div>
                            {message.courses.map((course, idx) => (
                                <CourseCard key={idx} course={course} />
                            ))}
                        </div>
                    )}

                    {/* 피드백 버튼 (봇 메시지만) */}
                    {!message.isUser && (
                        <div className="flex items-center gap-2 px-2">
                            {/* 타임스탬프 */}
                            {message.timestamp && (
                                <span className="text-xs text-gray-400">
                                    {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </span>
                            )}

                            {/* 피드백 버튼 */}
                            <div className="flex items-center gap-1 ml-auto">
                                <button
                                    onClick={() => handleFeedback('like')}
                                    className={`p-1.5 rounded-lg transition-all duration-200 ${feedback === 'like'
                                            ? 'bg-green-100 text-green-600'
                                            : 'hover:bg-gray-100 text-gray-400 hover:text-green-600'
                                        }`}
                                    title="도움이 됐어요"
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                                    </svg>
                                </button>
                                <button
                                    onClick={() => handleFeedback('dislike')}
                                    className={`p-1.5 rounded-lg transition-all duration-200 ${feedback === 'dislike'
                                            ? 'bg-red-100 text-red-600'
                                            : 'hover:bg-gray-100 text-gray-400 hover:text-red-600'
                                        }`}
                                    title="개선이 필要해요"
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                                    </svg>
                                </button>
                            </div>

                            {/* 피드백 감사 메시지 */}
                            {showFeedback && (
                                <span className="text-xs text-green-600 animate-fade-in">
                                    피드백 감사합니다!
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MessageBubble;