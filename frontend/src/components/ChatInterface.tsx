import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from '../api/chat';
import MessageBubble from './MessageBubble';
import MapButton from './MapButton';
import RequirementsCard from './RequirementsCard';
import EvaluationCard from './EvaluationCard';

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    timestamp?: string;
    classroomInfo?: any;
    mapLink?: string;
    showMapButton?: boolean;
    notices?: any[];
    seats?: any[];
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

// 빠른 질문 버튼
const QUICK_QUESTIONS = [
    { emoji: '📍', text: '전101 어디야', category: 'classroom' },
    { emoji: '📚', text: '자료구조 몇 학점?', category: 'curriculum' },
    { emoji: '📢', text: '최신 공지사항', category: 'notice' },
    { emoji: '💺', text: '도서관 자리 있어?', category: 'library' },
    { emoji: '🚌', text: '셔틀버스 시간표', category: 'shuttle' },
    { emoji: '🎓', text: '졸업요건 알려줘', category: 'requirement' },
];

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showWelcome, setShowWelcome] = useState(true);
    const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);

    // 도서관 로그인 상태
    const [showLibraryLogin, setShowLibraryLogin] = useState(false);
    const [libraryCredentials, setLibraryCredentials] = useState({
        username: '',
        password: ''
    });
    const [pendingLibraryMessage, setPendingLibraryMessage] = useState('');

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // 사용자 위치 가져오기
    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setUserLocation({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    });
                },
                (error) => {
                    console.log('⚠️ 위치 권한 거부:', error.message);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                }
            );
        }
    }, []);

    // 빠른 질문 클릭
    const handleQuickQuestion = (question: string) => {
        setInputValue(question);
        setShowWelcome(false);
        inputRef.current?.focus();
        // 자동 전송
        setTimeout(() => handleSend(false, question), 100);
    };

    const handleSend = async (withCredentials: boolean = false, customMessage?: string) => {
        const messageToSend = customMessage || (withCredentials ? pendingLibraryMessage : inputValue);

        if (!messageToSend.trim()) return;

        // 환영 메시지 숨김
        setShowWelcome(false);

        // 로그인 폼 전송이 아닌 경우에만 사용자 메시지 추가
        if (!withCredentials) {
            const userMessage: Message = {
                id: Date.now().toString(),
                text: messageToSend,
                isUser: true,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, userMessage]);
            setInputValue('');
        }

        setIsLoading(true);

        try {
            const response = await sendMessage(
                messageToSend,
                userLocation?.latitude,
                userLocation?.longitude,
                withCredentials ? libraryCredentials.username : undefined,
                withCredentials ? libraryCredentials.password : undefined
            );

            // 로그인 필요 감지
            if (response.message.includes('학번') && response.message.includes('비밀번호') && !withCredentials) {
                setShowLibraryLogin(true);
                setPendingLibraryMessage(messageToSend);

                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: response.message,
                    isUser: false,
                    timestamp: new Date().toISOString(),
                    needs_library_login: true,
                    pending_message: messageToSend
                };
                setMessages((prev) => [...prev, aiMessage]);
            } else {
                // 로그인 성공 또는 로그인 불필요한 경우
                if (withCredentials) {
                    setShowLibraryLogin(false);
                    setLibraryCredentials({ username: '', password: '' });
                    setPendingLibraryMessage('');
                }

                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: response.message,
                    isUser: false,
                    timestamp: new Date().toISOString(),
                    classroomInfo: response.classroom,
                    mapLink: response.map_link,
                    showMapButton: response.show_map_button,
                    notices: response.notices,
                    seats: response.seats,
                    requirements: response.requirements,
                    show_requirements: response.show_requirements,
                    evaluation: response.evaluation,
                    show_evaluation: response.show_evaluation,
                    library_info: response.library_info,
                    show_library_info: response.show_library_info,
                    library_seats: response.library_seats,
                    show_library_seats: response.show_library_seats,
                    library_reservation_url: response.library_reservation_url,
                    show_reservation_button: response.show_reservation_button,
                };

                setMessages((prev) => [...prev, aiMessage]);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                isUser: false,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);

            // 로그인 폼도 닫기
            if (withCredentials) {
                setShowLibraryLogin(false);
                setLibraryCredentials({ username: '', password: '' });
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleLibraryLogin = () => {
        if (libraryCredentials.username && libraryCredentials.password) {
            handleSend(true);
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 180px)' }}>
            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 scrollbar-custom">
                {/* 환영 메시지 */}
                {showWelcome && messages.length === 0 && (
                    <div className="animate-fade-in">
                        {/* 환영 헤더 */}
                        <div className="text-center mb-8 pt-8">
                            <div className="inline-block p-4 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-2xl mb-4 shadow-lg">
                                <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                                </svg>
                            </div>
                            <h2 className="text-2xl sm:text-3xl font-bold text-khu-primary mb-2">
                                안녕하세요! 👋
                            </h2>
                            <p className="text-gray-600 text-sm sm:text-base">
                                경희대학교 캠퍼스 정보를 안내하는 AI 어시스턴트입니다
                            </p>
                        </div>

                        {/* 빠른 질문 */}
                        <div className="mb-6">
                            <h3 className="text-sm font-semibold text-gray-700 mb-3 px-2">
                                💡 자주 묻는 질문
                            </h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {QUICK_QUESTIONS.map((q, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleQuickQuestion(q.text)}
                                        className="btn-quick text-left"
                                    >
                                        <span className="text-lg mr-2">{q.emoji}</span>
                                        <span className="text-sm">{q.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* 기능 안내 */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 px-2">
                            <div className="p-4 bg-khu-red-50 rounded-xl border border-khu-red-100">
                                <div className="text-2xl mb-2">🎯</div>
                                <h4 className="font-semibold text-gray-800 mb-1">강의실 검색</h4>
                                <p className="text-xs text-gray-600">전자정보대 강의실 위치와 길찾기</p>
                            </div>
                            <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                                <div className="text-2xl mb-2">📚</div>
                                <h4 className="font-semibold text-gray-800 mb-1">교과과정 조회</h4>
                                <p className="text-xs text-gray-600">과목 학점, 개설학기 정보</p>
                            </div>
                            <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                                <div className="text-2xl mb-2">📢</div>
                                <h4 className="font-semibold text-gray-800 mb-1">공지사항</h4>
                                <p className="text-xs text-gray-600">학과 및 학교 최신 공지</p>
                            </div>
                            <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
                                <div className="text-2xl mb-2">🚌</div>
                                <h4 className="font-semibold text-gray-800 mb-1">캠퍼스 정보</h4>
                                <p className="text-xs text-gray-600">셔틀, 도서관, 학식 메뉴</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* 대화 메시지 */}
                {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                ))}

                {/* 로딩 애니메이션 */}
                {isLoading && (
                    <div className="flex items-start gap-2 animate-slide-up">
                        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-khu-primary to-khu-red-600 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md">
                            AI
                        </div>
                        <div className="bg-white rounded-bubble px-5 py-4 shadow-md">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">답변 생성 중...</p>
                        </div>
                    </div>
                )}

                {/* 도서관 로그인 폼 */}
                {showLibraryLogin && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 animate-slide-up">
                        <div className="flex items-start gap-3 mb-4">
                            <div className="text-2xl">🔐</div>
                            <div>
                                <h3 className="font-semibold text-gray-800 mb-1">도서관 로그인 필요</h3>
                                <p className="text-sm text-gray-600">
                                    도서관 좌석 조회를 위해 학번과 비밀번호를 입력해주세요
                                </p>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <input
                                type="text"
                                placeholder="학번"
                                value={libraryCredentials.username}
                                onChange={(e) => setLibraryCredentials({
                                    ...libraryCredentials,
                                    username: e.target.value
                                })}
                                className="input-chat"
                            />
                            <input
                                type="password"
                                placeholder="비밀번호"
                                value={libraryCredentials.password}
                                onChange={(e) => setLibraryCredentials({
                                    ...libraryCredentials,
                                    password: e.target.value
                                })}
                                className="input-chat"
                                onKeyPress={(e) => e.key === 'Enter' && handleLibraryLogin()}
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleLibraryLogin}
                                    disabled={!libraryCredentials.username || !libraryCredentials.password}
                                    className="btn-primary flex-1"
                                >
                                    확인
                                </button>
                                <button
                                    onClick={() => {
                                        setShowLibraryLogin(false);
                                        setLibraryCredentials({ username: '', password: '' });
                                    }}
                                    className="btn-secondary"
                                >
                                    취소
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* 입력 영역 */}
            <div className="border-t border-gray-200 bg-white p-4">
                {/* 위치 상태 */}
                {userLocation && (
                    <div className="mb-3 flex items-center gap-2 text-xs text-green-600">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        <span>현재 위치 확인됨 - 길찾기 가능</span>
                    </div>
                )}

                {/* 입력창 */}
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="궁금한 것을 물어보세요... (예: 전101 어디야)"
                        className="input-chat"
                        disabled={isLoading}
                    />
                    <button
                        onClick={() => handleSend()}
                        disabled={isLoading || !inputValue.trim()}
                        className="btn-primary px-6 flex-shrink-0"
                    >
                        {isLoading ? (
                            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        ) : (
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                            </svg>
                        )}
                    </button>
                </div>

                {/* 도움말 */}
                <p className="mt-2 text-xs text-gray-500 text-center">
                    Enter로 전송 · Shift+Enter로 줄바꿈
                </p>
            </div>
        </div>
    );
};

export default ChatInterface;