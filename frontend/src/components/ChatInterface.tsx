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
    library_reservation_url?: string;  // 🆕 추가
    show_reservation_button?: boolean;  // 🆕 추가
}

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: '안녕하세요! 경희대 강의실 위치와 학생회 공지사항을 안내해드립니다. 궁금하신 내용을 말씀해주세요!\n\n예시:\n• 전101 어디야?\n• 최근 공지 알려줘\n• 학생회비 관련 공지 찾아줘\n• 도서관 운영시간 알려줘\n• 도서관 좌석 있어?',
            isUser: false,
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);

    // 🆕 도서관 로그인 상태
    const [showLibraryLogin, setShowLibraryLogin] = useState(false);
    const [libraryCredentials, setLibraryCredentials] = useState({
        username: '',
        password: ''
    });
    const [pendingLibraryMessage, setPendingLibraryMessage] = useState('');

    const messagesEndRef = useRef<HTMLDivElement>(null);

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
                    console.log('✅ 위치 획득:', position.coords.latitude, position.coords.longitude);
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

    const handleSend = async (withCredentials: boolean = false) => {
        const messageToSend = withCredentials ? pendingLibraryMessage : inputValue;

        if (!messageToSend.trim()) return;

        // 로그인 폼 전송이 아닌 경우에만 사용자 메시지 추가
        if (!withCredentials) {
            const userMessage: Message = {
                id: Date.now().toString(),
                text: messageToSend,
                isUser: true,
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

            // 🆕 로그인 필요 감지
            if (response.message.includes('학번') && response.message.includes('비밀번호') && !withCredentials) {
                setShowLibraryLogin(true);
                setPendingLibraryMessage(messageToSend);

                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: response.message,
                    isUser: false,
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
                    classroomInfo: response.classroom,
                    mapLink: response.map_link,
                    showMapButton: response.show_map_button,
                    notices: response.notices,
                    seats: response.seats,  // 🆕 좌석 정보 추가
                    requirements: response.requirements,
                    show_requirements: response.show_requirements,
                    evaluation: response.evaluation,
                    show_evaluation: response.show_evaluation,
                    library_info: response.library_info,
                    show_library_info: response.show_library_info,
                    library_seats: response.library_seats,
                    show_library_seats: response.show_library_seats,
                    library_reservation_url: response.library_reservation_url,  // 🆕 추가
                    show_reservation_button: response.show_reservation_button,  // 🆕 추가
                };

                setMessages((prev) => [...prev, aiMessage]);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
                isUser: false,
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

    const handleLibraryLogin = () => {
        if (!libraryCredentials.username || !libraryCredentials.password) {
            alert('학번과 비밀번호를 모두 입력해주세요.');
            return;
        }
        handleSend(true);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div key={message.id}>
                        <MessageBubble message={message} />

                        {/* 🆕 도서관 로그인 폼 (메시지 안에 표시) */}
                        {message.needs_library_login && showLibraryLogin && (
                            <div className="mt-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <div className="mb-3 font-semibold text-blue-900">
                                    🔐 도서관 로그인
                                </div>
                                <input
                                    type="text"
                                    placeholder="학번"
                                    value={libraryCredentials.username}
                                    onChange={(e) => setLibraryCredentials({
                                        ...libraryCredentials,
                                        username: e.target.value
                                    })}
                                    className="w-full px-3 py-2 mb-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={isLoading}
                                />
                                <input
                                    type="password"
                                    placeholder="비밀번호"
                                    value={libraryCredentials.password}
                                    onChange={(e) => setLibraryCredentials({
                                        ...libraryCredentials,
                                        password: e.target.value
                                    })}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            handleLibraryLogin();
                                        }
                                    }}
                                    className="w-full px-3 py-2 mb-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={isLoading}
                                />
                                <div className="flex space-x-2">
                                    <button
                                        onClick={handleLibraryLogin}
                                        disabled={isLoading || !libraryCredentials.username || !libraryCredentials.password}
                                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {isLoading ? '로그인 중...' : '로그인하고 조회하기'}
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowLibraryLogin(false);
                                            setLibraryCredentials({ username: '', password: '' });
                                            setPendingLibraryMessage('');
                                        }}
                                        disabled={isLoading}
                                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                                    >
                                        취소
                                    </button>
                                </div>
                                <div className="mt-2 text-xs text-gray-600">
                                    💡 Info21 통합 ID와 비밀번호를 입력하세요
                                </div>
                            </div>
                        )}

                        {/* 🆕 도서관 정보 카드 - 좌석 현황이 없고 로그인 폼도 없을 때만 표시 */}
                        {message.show_library_info && message.library_info && !message.show_library_seats && !message.needs_library_login && (
                            <div className="mt-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                                <h3 className="font-bold text-lg mb-2">📚 {message.library_info.name}</h3>
                                <div className="space-y-1 text-sm">
                                    <p><span className="font-semibold">캠퍼스:</span> {message.library_info.campus}</p>
                                    <p><span className="font-semibold">주소:</span> {message.library_info.address}</p>
                                    <p><span className="font-semibold">전화:</span> {message.library_info.phone}</p>
                                    <p><span className="font-semibold">평일:</span> {message.library_info.hours.weekday}</p>
                                    <p><span className="font-semibold">주말:</span> {message.library_info.hours.weekend}</p>
                                </div>
                                {message.library_info.floors && message.library_info.floors.length > 0 && (
                                    <div className="mt-3">
                                        <p className="font-semibold mb-1">열람실 정보:</p>
                                        <div className="space-y-1 text-sm">
                                            {message.library_info.floors.map((floor: any, idx: number) => (
                                                <div key={idx} className="pl-2">
                                                    • {floor.name}: {floor.total_seats}석 ({floor.hours})
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 🆕 좌석 현황 카드 */}
                        {message.show_library_seats && message.library_seats && (
                            <div className="mt-3 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                                <h3 className="font-bold text-lg mb-2">🪑 {message.library_seats.library} 좌석 현황</h3>
                                <div className="mb-3 p-3 bg-white rounded">
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>전체: {message.library_seats.total_seats}석</span>
                                        <span className="text-blue-600">이용 가능: {message.library_seats.available}석</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full"
                                            style={{ width: `${(message.library_seats.available / message.library_seats.total_seats) * 100}%` }}
                                        ></div>
                                    </div>
                                    <div className="text-xs text-gray-600 mt-1">
                                        이용률: {message.library_seats.occupancy_rate}%
                                    </div>
                                </div>
                                {message.library_seats.floors && message.library_seats.floors.length > 0 && (
                                    <div className="space-y-2">
                                        {message.library_seats.floors.map((floor: any, idx: number) => (
                                            <div key={idx} className="p-2 bg-white rounded text-sm">
                                                <div className="flex justify-between mb-1">
                                                    <span className="font-semibold">{floor.name}</span>
                                                    <span className="text-blue-600">{floor.available}/{floor.total}석</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-1.5">
                                                    <div
                                                        className="bg-green-500 h-1.5 rounded-full"
                                                        style={{ width: `${(floor.available / floor.total) * 100}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* 🆕 도서관 예약 버튼 추가 */}
                                {message.show_reservation_button && message.library_reservation_url && (
                                    <a
                                        href={message.library_reservation_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-4 inline-flex items-center justify-center w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md"
                                    >
                                        <svg
                                            className="w-5 h-5 mr-2"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                                            />
                                        </svg>
                                        도서관 좌석 예약하러 가기
                                    </a>
                                )}
                            </div>
                        )}

                        {/* 🆕 일반 좌석 정보 (seats 필드) */}
                        {message.seats && message.seats.length > 0 && !message.show_library_seats && (
                            <div className="mt-3 space-y-2">
                                <div className="font-semibold text-gray-700">
                                    📚 도서관 좌석 현황
                                </div>
                                {message.seats.map((seat: any, idx: number) => (
                                    <div
                                        key={idx}
                                        className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                                    >
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <span className="font-medium text-gray-900">
                                                    {seat.location}
                                                </span>
                                                {seat.floor && (
                                                    <span className="ml-2 text-sm text-gray-600">
                                                        {seat.floor}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-right">
                                                <div className="text-lg font-bold text-blue-600">
                                                    {seat.available_seats} / {seat.total_seats}
                                                </div>
                                                <div className="text-xs text-gray-500">
                                                    남은 좌석
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {/* 🆕 예약 버튼 (일반 좌석 정보에도 추가) */}
                                {message.show_reservation_button && message.library_reservation_url && (
                                    <a
                                        href={message.library_reservation_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-3 inline-flex items-center justify-center w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md"
                                    >
                                        <svg
                                            className="w-5 h-5 mr-2"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                                            />
                                        </svg>
                                        도서관 좌석 예약하러 가기
                                    </a>
                                )}
                            </div>
                        )}

                        {message.showMapButton && message.mapLink && (
                            <MapButton mapLink={message.mapLink} />
                        )}
                        {message.show_requirements && message.requirements && (
                            <div className="mt-3">
                                <RequirementsCard data={message.requirements} />
                            </div>
                        )}

                        {message.show_evaluation && message.evaluation && (
                            <div className="mt-3">
                                <EvaluationCard data={message.evaluation} />
                            </div>
                        )}
                    </div>
                ))}
                {isLoading && (
                    <div className="flex items-start space-x-2">
                        <div className="bg-gray-200 rounded-lg px-4 py-3 max-w-[70%]">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* 입력 영역 */}
            <div className="border-t p-4">
                {userLocation && (
                    <div className="mb-2 text-xs text-green-600">
                        📍 현재 위치 확인됨 - 길찾기 가능
                    </div>
                )}
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="강의실이나 공지사항을 물어보세요 (예: 전101, 최근 공지, 도서관 좌석)"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isLoading}
                    />
                    <button
                        onClick={() => handleSend(false)}
                        disabled={isLoading || !inputValue.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        전송
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;