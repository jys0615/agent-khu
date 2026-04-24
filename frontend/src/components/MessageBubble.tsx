import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import NoticeCard from './NoticeCard';
import MealCard from './MealCard';
import LibrarySeatCard from './LibrarySeatCard';
import ShuttleCard from './ShuttleCard';
import CourseCard from './CourseCard';
import MapButton from './MapButton';
import MagnoliaLogo from './MagnoliaLogo';

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
        library_info?: any;
        show_library_info?: boolean;
        library_seats?: any;
        show_library_seats?: boolean;
        library_reservation_url?: string;
        show_reservation_button?: boolean;
        requirements?: any;
        show_requirements?: boolean;
        evaluation?: any;
        show_evaluation?: boolean;
    };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const [feedback, setFeedback] = useState<'like' | 'dislike' | null>(null);
    const [copied, setCopied] = useState(false);

    const handleFeedback = (type: 'like' | 'dislike') => {
        setFeedback(type);
        console.log('Feedback:', type);
    };

    const handleCopy = async () => {
        if (!message.text) return;
        try {
            await navigator.clipboard.writeText(message.text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            // clipboard API 미지원 환경
        }
    };

    /* ── 사용자 메시지 ──────────────────────────────────── */
    if (message.isUser) {
        return (
            <div className="flex justify-end animate-slide-up">
                <div className="bubble-user">
                    <div className="prose-custom prose-user text-sm leading-relaxed">
                        <ReactMarkdown
                            components={{
                                p: ({ node, ...props }) => (
                                    <p className="whitespace-pre-wrap mb-1.5 last:mb-0" {...props}/>
                                ),
                            }}
                        >
                            {message.text}
                        </ReactMarkdown>
                    </div>
                    {message.timestamp && (
                        <p className="text-[10px] text-white/50 mt-1.5 text-right">
                            {new Date(message.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                        </p>
                    )}
                </div>
            </div>
        );
    }

    /* ── 봇 메시지 ──────────────────────────────────────── */
    return (
        <div className="flex items-start gap-2.5 animate-slide-up group">

            {/* AI 아바타 */}
            <div className="flex-shrink-0 mt-0.5">
                <MagnoliaLogo size={28} />
            </div>

            <div className="flex flex-col gap-3 flex-1 min-w-0">

                {/* 메인 말풍선 */}
                <div className="bubble-bot relative">

                    {/* Tool 실행 상태 */}
                    {message.activeTools && message.activeTools.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-3">
                            {message.activeTools.map((label, i) => (
                                <span key={i} className="tool-pill">
                                    <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-30" cx="12" cy="12" r="10"
                                                stroke="currentColor" strokeWidth="3"/>
                                        <path className="opacity-80" fill="currentColor"
                                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                    </svg>
                                    {label}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* 텍스트 */}
                    {(message.text || message.isStreaming) && (
                        <div className="prose-custom text-sm">
                            <ReactMarkdown
                                components={{
                                    p: ({ node, ...props }) => (
                                        <p className="whitespace-pre-wrap mb-2 last:mb-0 leading-relaxed" {...props}/>
                                    ),
                                    strong: ({ node, ...props }) => (
                                        <strong className="font-semibold text-khu-primary" {...props}/>
                                    ),
                                    h1: ({ node, ...props }) => (
                                        <h1 className="text-base font-bold text-khu-primary mt-3 mb-1.5 first:mt-0" {...props}/>
                                    ),
                                    h2: ({ node, ...props }) => (
                                        <h2 className="text-sm font-bold text-khu-primary mt-2.5 mb-1 first:mt-0" {...props}/>
                                    ),
                                    h3: ({ node, ...props }) => (
                                        <h3 className="text-sm font-semibold text-gray-700 mt-2 mb-1 first:mt-0" {...props}/>
                                    ),
                                    a: ({ node, ...props }) => (
                                        <a className="text-khu-navy underline hover:text-khu-primary transition-colors" {...props}/>
                                    ),
                                    ul: ({ node, ...props }) => (
                                        <ul className="list-disc ml-4 space-y-0.5 mb-2" {...props}/>
                                    ),
                                    ol: ({ node, ...props }) => (
                                        <ol className="list-decimal ml-4 space-y-0.5 mb-2" {...props}/>
                                    ),
                                    li: ({ node, ...props }) => (
                                        <li className="leading-relaxed" {...props}/>
                                    ),
                                    code: ({ node, ...props }) => (
                                        <code className="bg-gray-100 px-1.5 py-0.5 rounded-md text-xs font-mono text-gray-700" {...props}/>
                                    ),
                                    hr: ({ node, ...props }) => (
                                        <hr className="border-gray-200 my-2" {...props}/>
                                    ),
                                }}
                            >
                                {message.text}
                            </ReactMarkdown>
                            {/* 스트리밍 커서 */}
                            {message.isStreaming && <span className="streaming-cursor"/>}
                        </div>
                    )}

                    {/* 강의실 정보 */}
                    {message.classroomInfo && (
                        <div className="mt-3 p-3 bg-khu-50 rounded-xl border border-khu-100">
                            <p className="text-sm font-semibold text-khu-primary flex items-center gap-1.5">
                                <span>📍</span>
                                {message.classroomInfo.code} — {message.classroomInfo.room_name}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                                {message.classroomInfo.floor}층 · {message.classroomInfo.building_name}
                            </p>
                            {message.showMapButton && <MapButton mapLink={message.mapLink}/>}
                        </div>
                    )}

                    {/* 복사 버튼 (hover시 노출) */}
                    {message.text && !message.isStreaming && (
                        <button
                            onClick={handleCopy}
                            className="copy-btn absolute top-2.5 right-2.5"
                            title="복사"
                        >
                            {copied ? (
                                <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                                </svg>
                            ) : (
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                                    <path strokeLinecap="round" strokeLinejoin="round"
                                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                </svg>
                            )}
                        </button>
                    )}
                </div>

                {/* ── Rich content cards ── */}

                {(message.notices?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                        <SectionLabel icon="📢" title="공지사항" count={message.notices!.length}/>
                        {message.notices!.map((n, i) => <NoticeCard key={i} notice={n}/>)}
                    </div>
                )}

                {(message.meals?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                        <SectionLabel icon="🍚" title="학식 메뉴" count={message.meals!.length}/>
                        {message.meals!.map((m, i) => <MealCard key={i} meal={m}/>)}
                    </div>
                )}

                {(message.seats?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                        <SectionLabel icon="📚" title="도서관 좌석" count={message.seats!.length}/>
                        {message.seats!.map((s, i) => <LibrarySeatCard key={i} seat={s}/>)}
                    </div>
                )}

                {message.shuttle && (
                    <div>
                        <SectionLabel icon="🚌" title="다음 버스"/>
                        <ShuttleCard shuttle={message.shuttle}/>
                    </div>
                )}

                {(message.shuttles?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                        <SectionLabel icon="🚌" title="셔틀버스"/>
                        {message.shuttles!.map((s, i) => <ShuttleCard key={i} shuttle={s}/>)}
                    </div>
                )}

                {(message.courses?.length ?? 0) > 0 && (
                    <div className="space-y-2">
                        <SectionLabel icon="📖" title="강의 목록" count={message.courses!.length}/>
                        {message.courses!.map((c, i) => <CourseCard key={i} course={c}/>)}
                    </div>
                )}

                {/* 하단 메타 (타임스탬프 + 피드백) */}
                {!message.isStreaming && (
                    <div className="flex items-center justify-between px-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <span className="text-[10px] text-gray-400">
                            {message.timestamp
                                ? new Date(message.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
                                : ''}
                        </span>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => handleFeedback('like')}
                                className={`p-1.5 rounded-lg transition-all ${
                                    feedback === 'like'
                                        ? 'bg-green-100 text-green-600'
                                        : 'text-gray-300 hover:text-green-500 hover:bg-green-50'
                                }`}
                                title="도움이 됐어요"
                            >
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z"/>
                                </svg>
                            </button>
                            <button
                                onClick={() => handleFeedback('dislike')}
                                className={`p-1.5 rounded-lg transition-all ${
                                    feedback === 'dislike'
                                        ? 'bg-red-100 text-red-500'
                                        : 'text-gray-300 hover:text-red-400 hover:bg-red-50'
                                }`}
                                title="개선이 필요해요"
                            >
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

/* ── 섹션 레이블 ─────────────────────────────────────────── */
const SectionLabel: React.FC<{ icon: string; title: string; count?: number }> = ({ icon, title, count }) => (
    <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-sm">{icon}</span>
        <span className="text-xs font-semibold text-gray-700">{title}</span>
        {count !== undefined && (
            <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">
                {count}개
            </span>
        )}
    </div>
);

export default MessageBubble;
