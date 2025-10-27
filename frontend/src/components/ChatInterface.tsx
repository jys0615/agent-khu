import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from '../api/chat';
import MessageBubble from './MessageBubble';
import MapButton from './MapButton';

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    classroomInfo?: any;
    mapLink?: string;
    showMapButton?: boolean;
    notices?: any[];
}

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: '안녕하세요! 경희대 강의실 위치와 학생회 공지사항을 안내해드립니다. 궁금하신 내용을 말씀해주세요!\n\n예시:\n• 전101 어디야?\n• 최근 공지 알려줘\n• 학생회비 관련 공지 찾아줘',
            isUser: false,
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
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

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: inputValue,
            isUser: true,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await sendMessage(
                inputValue,
                userLocation?.latitude,
                userLocation?.longitude
            );

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: response.message,
                isUser: false,
                classroomInfo: response.classroom,
                mapLink: response.map_link,
                showMapButton: response.show_map_button,
                notices: response.notices,
            };

            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
                isUser: false,
            };
            setMessages((prev) => [...prev, errorMessage]);
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

    return (
        <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div key={message.id}>
                        <MessageBubble message={message} />
                        {message.showMapButton && message.mapLink && (
                            <MapButton mapLink={message.mapLink} />
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
                        placeholder="강의실이나 공지사항을 물어보세요 (예: 전101, 최근 공지)"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
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