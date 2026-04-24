import React, { useState, useRef, useEffect, useCallback } from 'react';
import { sendMessageStream } from '../api/chat';
import { useAuth } from '../contexts/AuthContext';
import MessageBubble from './MessageBubble';
import MagnoliaLogo from './MagnoliaLogo';

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    isStreaming?: boolean;
    activeTools?: string[];
    timestamp?: string;
    classroomInfo?: any;
    mapLink?: string;
    showMapButton?: boolean;
    notices?: any[];
    meals?: any[];
    seats?: any[];
    shuttle?: any;
    shuttles?: any[];
    courses?: any[];
    requirements?: any;
    show_requirements?: boolean;
    evaluation?: any;
    show_evaluation?: boolean;
    library_info?: any;
    show_library_info?: boolean;
    library_seats?: any;
    show_library_seats?: boolean;
    needs_library_login?: boolean;
    pending_message?: string;
    library_reservation_url?: string;
    show_reservation_button?: boolean;
}

const FEATURES = [
    {
        icon: '🏛', title: '강의실',
        desc: '위치 & 길찾기',
        q: '전자정보대학관 1층 강의실 어디야?',
    },
    {
        icon: '🍽', title: '학식',
        desc: '오늘의 메뉴',
        q: '오늘 학식 메뉴 뭐야?',
    },
    {
        icon: '📚', title: '도서관',
        desc: '좌석 조회 & 예약',
        q: '도서관 열람실 빈자리 있어?',
    },
    {
        icon: '📢', title: '공지사항',
        desc: '최신 학사 공지',
        q: '최신 공지사항 알려줘',
    },
    {
        icon: '🎓', title: '졸업요건',
        desc: '이수 기준 확인',
        q: '졸업요건 알려줘',
    },
    {
        icon: '🚌', title: '셔틀버스',
        desc: '운행 시간표',
        q: '셔틀버스 언제 와?',
    },
];

const QUICK_QS = [
    '오늘 학식 뭐야',
    '도서관 빈자리 알려줘',
    '컴퓨터공학부 전공 과목 검색',
    '졸업요건 알려줘',
    '최신 공지사항',
];

const ChatInterface: React.FC = () => {
    const { user } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showWelcome, setShowWelcome] = useState(true);
    const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);

    const [showLibraryLogin, setShowLibraryLogin] = useState(false);
    const [libraryCredentials, setLibraryCredentials] = useState({ username: '', password: '' });
    const [pendingLibraryMessage, setPendingLibraryMessage] = useState('');

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

    // 위치 취득
    useEffect(() => {
        navigator.geolocation?.getCurrentPosition(
            (pos) => setUserLocation({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
            () => {},
            { enableHighAccuracy: true, timeout: 5000 },
        );
    }, []);

    // textarea 자동 높이
    const resizeTextarea = () => {
        const el = textareaRef.current;
        if (el) {
            el.style.height = 'auto';
            el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputValue(e.target.value);
        resizeTextarea();
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setShowWelcome(true);
        setInputValue('');
        setShowLibraryLogin(false);
        textareaRef.current?.focus();
    };

    const handleSend = async (withCredentials = false, customMessage?: string) => {
        const messageToSend = customMessage || (withCredentials ? pendingLibraryMessage : inputValue);
        if (!messageToSend.trim() || isLoading) return;

        setShowWelcome(false);

        if (!withCredentials) {
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                text: messageToSend,
                isUser: true,
                timestamp: new Date().toISOString(),
            }]);
            setInputValue('');
            if (textareaRef.current) textareaRef.current.style.height = 'auto';
        }

        setIsLoading(true);

        const aiMsgId = `ai-${Date.now()}`;
        setMessages(prev => [...prev, {
            id: aiMsgId, text: '', isUser: false, isStreaming: true, activeTools: [],
        }]);

        try {
            await sendMessageStream(
                messageToSend,
                (event) => {
                    if (event.type === 'text') {
                        setMessages(prev => prev.map(m =>
                            m.id === aiMsgId ? { ...m, text: m.text + event.delta } : m,
                        ));
                    } else if (event.type === 'tool_start') {
                        setMessages(prev => prev.map(m =>
                            m.id === aiMsgId
                                ? { ...m, activeTools: [...(m.activeTools ?? []), event.label] }
                                : m,
                        ));
                    } else if (event.type === 'tool_end') {
                        setMessages(prev => prev.map(m =>
                            m.id === aiMsgId
                                ? { ...m, activeTools: (m.activeTools ?? []).slice(1) }
                                : m,
                        ));
                    } else if (event.type === 'done') {
                        const r = event.result as any;
                        // 도서관 로그인 필요 감지
                        if (
                            typeof r.message === 'string' &&
                            r.message.includes('학번') &&
                            r.message.includes('비밀번호') &&
                            !withCredentials
                        ) {
                            setShowLibraryLogin(true);
                            setPendingLibraryMessage(messageToSend);
                            setMessages(prev => prev.map(m =>
                                m.id === aiMsgId
                                    ? { ...m, text: r.message, isStreaming: false, activeTools: [],
                                        needs_library_login: true, pending_message: messageToSend }
                                    : m,
                            ));
                            return;
                        }
                        if (withCredentials) {
                            setShowLibraryLogin(false);
                            setLibraryCredentials({ username: '', password: '' });
                            setPendingLibraryMessage('');
                        }
                        setMessages(prev => prev.map(m =>
                            m.id === aiMsgId
                                ? {
                                    ...m,
                                    text: r.message ?? m.text,
                                    isStreaming: false,
                                    activeTools: [],
                                    timestamp: new Date().toISOString(),
                                    classroomInfo: r.classroom,
                                    mapLink: r.map_link,
                                    showMapButton: r.show_map_button,
                                    notices: r.notices,
                                    meals: r.meals,
                                    seats: r.seats,
                                    shuttle: r.next_bus,
                                    shuttles: r.shuttles,
                                    courses: r.courses,
                                    requirements: r.requirements,
                                    show_requirements: r.show_requirements,
                                    evaluation: r.evaluation,
                                    show_evaluation: r.show_evaluation,
                                    library_info: r.library_info,
                                    show_library_info: r.show_library_info,
                                    library_seats: r.library_seats,
                                    show_library_seats: r.show_library_seats,
                                    library_reservation_url: r.library_reservation_url,
                                    show_reservation_button: r.show_reservation_button,
                                  }
                                : m,
                        ));
                    } else if (event.type === 'error') {
                        setMessages(prev => prev.map(m =>
                            m.id === aiMsgId
                                ? { ...m, text: '죄송합니다. 일시적인 오류가 발생했습니다.', isStreaming: false, activeTools: [] }
                                : m,
                        ));
                    }
                },
                userLocation?.latitude,
                userLocation?.longitude,
                withCredentials ? libraryCredentials.username : undefined,
                withCredentials ? libraryCredentials.password : undefined,
            );
        } catch (err) {
            console.error('Stream error:', err);
            setMessages(prev => prev.map(m =>
                m.id === aiMsgId
                    ? { ...m, text: '죄송합니다. 네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                        isStreaming: false, activeTools: [] }
                    : m,
            ));
            if (withCredentials) {
                setShowLibraryLogin(false);
                setLibraryCredentials({ username: '', password: '' });
            }
        } finally {
            setIsLoading(false);
        }
    };

    const greeting = user?.name ? `안녕하세요, ${user.name}님!` : '안녕하세요!';

    return (
        <div className="flex flex-col bg-transparent" style={{ height: 'calc(100dvh - 64px)' }}>
            <div className="flex flex-col flex-1 rounded-2xl overflow-hidden bg-white shadow-glass border border-gray-100 min-h-0">

                {/* ── 메시지 영역 ─────────────────────────────────── */}
                <div className="flex-1 overflow-y-auto scrollbar-custom px-4 py-5 sm:px-6 space-y-5 min-h-0">

                    {/* 환영 화면 */}
                    {showWelcome && messages.length === 0 && (
                        <div className="animate-fade-in pt-4">

                            {/* Hero */}
                            <div className="text-center mb-8">
                                <MagnoliaLogo size={64} className="mx-auto mb-4" />
                                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                                    {greeting} 👋
                                </h2>
                                <p className="text-gray-500 text-sm sm:text-base max-w-sm mx-auto leading-relaxed">
                                    경희대학교 캠퍼스 정보를 물어보세요.
                                    AI가 실시간으로 답변해드립니다.
                                </p>
                            </div>

                            {/* 피처 카드 그리드 */}
                            <div className="grid grid-cols-3 sm:grid-cols-3 gap-2.5 mb-7 max-w-lg mx-auto">
                                {FEATURES.map((f) => (
                                    <button
                                        key={f.title}
                                        onClick={() => handleSend(false, f.q)}
                                        className="feature-card text-left"
                                    >
                                        <span className="text-2xl">{f.icon}</span>
                                        <div>
                                            <p className="text-xs font-semibold text-gray-800">{f.title}</p>
                                            <p className="text-[10px] text-gray-400 mt-0.5 leading-tight">{f.desc}</p>
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {/* 빠른 질문 */}
                            <div className="max-w-lg mx-auto">
                                <p className="text-xs font-medium text-gray-400 mb-2.5 uppercase tracking-wide">
                                    자주 묻는 질문
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    {QUICK_QS.map((q) => (
                                        <button
                                            key={q}
                                            onClick={() => handleSend(false, q)}
                                            className="btn-quick text-xs py-2 px-3"
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 대화 메시지 */}
                    {messages.map((msg) => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))}

                    {/* 도서관 로그인 폼 */}
                    {showLibraryLogin && (
                        <div className="bg-khu-gold-lt border border-khu-gold/30 rounded-2xl p-4 animate-slide-up">
                            <div className="flex items-start gap-3 mb-4">
                                <div className="text-2xl">🔐</div>
                                <div>
                                    <h3 className="font-semibold text-gray-800 text-sm">도서관 로그인 필요</h3>
                                    <p className="text-xs text-gray-500 mt-0.5">
                                        좌석 조회를 위해 학번과 비밀번호를 입력해주세요
                                    </p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <input
                                    type="text"
                                    placeholder="학번"
                                    value={libraryCredentials.username}
                                    onChange={(e) => setLibraryCredentials({ ...libraryCredentials, username: e.target.value })}
                                    className="input-chat text-sm"
                                />
                                <input
                                    type="password"
                                    placeholder="비밀번호"
                                    value={libraryCredentials.password}
                                    onChange={(e) => setLibraryCredentials({ ...libraryCredentials, password: e.target.value })}
                                    className="input-chat text-sm"
                                    onKeyDown={(e) => e.key === 'Enter' && libraryCredentials.username && handleSend(true)}
                                />
                                <div className="flex gap-2 pt-1">
                                    <button
                                        onClick={() => libraryCredentials.username && libraryCredentials.password && handleSend(true)}
                                        disabled={!libraryCredentials.username || !libraryCredentials.password}
                                        className="btn-primary flex-1 py-2 text-sm"
                                    >
                                        확인
                                    </button>
                                    <button
                                        onClick={() => { setShowLibraryLogin(false); setLibraryCredentials({ username: '', password: '' }); }}
                                        className="btn-secondary py-2 text-sm px-4"
                                    >
                                        취소
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef}/>
                </div>

                {/* ── 입력 영역 ────────────────────────────────────── */}
                <div className="border-t border-gray-100 bg-white px-4 py-3 sm:px-5">

                    {/* 위치 상태 */}
                    {userLocation && (
                        <div className="flex items-center gap-1.5 text-[11px] text-green-600 mb-2.5">
                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd"
                                      d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                                      clipRule="evenodd"/>
                            </svg>
                            <span>위치 확인됨 — 길찾기 가능</span>
                        </div>
                    )}

                    {/* 입력 박스 */}
                    <div className="flex items-end gap-2">
                        {/* 새 대화 버튼 */}
                        <button
                            onClick={handleNewChat}
                            disabled={messages.length === 0}
                            className="btn-icon flex-shrink-0 mb-0.5 disabled:opacity-30 disabled:pointer-events-none"
                            title="새 대화 시작"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round"
                                      d="M12 4v16m8-8H4"/>
                            </svg>
                        </button>

                        {/* Textarea */}
                        <div className="flex-1 relative">
                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                placeholder="궁금한 것을 입력하세요..."
                                disabled={isLoading}
                                rows={1}
                                className="w-full resize-none input-chat py-3 pr-12 leading-relaxed
                                           max-h-40 overflow-y-auto scrollbar-hide text-sm"
                                style={{ minHeight: '48px' }}
                            />
                        </div>

                        {/* 전송 버튼 */}
                        <button
                            onClick={() => handleSend()}
                            disabled={isLoading || !inputValue.trim()}
                            className="w-10 h-10 rounded-xl flex-shrink-0 flex items-center justify-center
                                       text-white transition-all duration-200 active:scale-90
                                       disabled:opacity-40 disabled:pointer-events-none"
                            style={{ background: 'linear-gradient(135deg, #8B1538, #6B1030)' }}
                        >
                            {isLoading ? (
                                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10"
                                            stroke="currentColor" strokeWidth="4"/>
                                    <path className="opacity-75" fill="currentColor"
                                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                </svg>
                            ) : (
                                <svg className="w-4 h-4 -rotate-45" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                </svg>
                            )}
                        </button>
                    </div>

                    {/* 하단 힌트 */}
                    <div className="flex items-center justify-between mt-2">
                        <p className="text-[11px] text-gray-400">
                            Enter 전송 · Shift+Enter 줄바꿈
                        </p>
                        <p className="text-[11px] text-gray-300 hidden sm:block">
                            Claude Sonnet 4 · MCP
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
