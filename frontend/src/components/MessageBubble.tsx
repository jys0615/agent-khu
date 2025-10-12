import React from 'react';

interface Notice {
    id: number;
    title: string;
    content: string;
    instagram_url: string;
    image_url?: string;
    posted_at: string;
    likes?: number;
    comments?: number;
}

interface MessageBubbleProps {
    message: {
        text: string;
        isUser: boolean;
        classroomInfo?: any;
        notices?: Notice[];
    };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    if (message.isUser) {
        return (
            <div className="flex justify-end">
                <div className="bg-blue-600 text-white rounded-lg px-4 py-3 max-w-[70%]">
                    <p className="whitespace-pre-wrap">{message.text}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-start space-x-2">
            <div className="bg-gray-200 rounded-lg px-4 py-3 max-w-[70%]">
                <p className="whitespace-pre-wrap text-gray-800">{message.text}</p>

                {message.classroomInfo && (
                    <div className="mt-3 p-3 bg-white rounded border border-gray-300">
                        <h4 className="font-semibold text-sm text-gray-700 mb-2">📍 강의실 정보</h4>
                        <div className="text-sm text-gray-600 space-y-1">
                            <p>
                                <span className="font-medium">코드:</span> {message.classroomInfo.code}
                            </p>
                            <p>
                                <span className="font-medium">건물:</span> {message.classroomInfo.building_name}
                            </p>
                            <p>
                                <span className="font-medium">호실:</span> {message.classroomInfo.room_number}호
                            </p>
                            <p>
                                <span className="font-medium">층:</span> {message.classroomInfo.floor}층
                            </p>
                            {message.classroomInfo.capacity && (
                                <p>
                                    <span className="font-medium">수용인원:</span> {message.classroomInfo.capacity}명
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {message.notices && message.notices.length > 0 && (
                    <div className="mt-3 space-y-2">
                        <h4 className="font-semibold text-sm text-gray-700 mb-2">📢 공지사항</h4>
                        {message.notices.map((notice) => (
                            <div
                                key={notice.id}
                                className="bg-white rounded-lg border border-gray-300 overflow-hidden hover:shadow-md transition-shadow"
                            >
                                {notice.image_url && (
                                    <img
                                        src={notice.image_url}
                                        alt={notice.title}
                                        className="w-full h-48 object-cover"
                                    />
                                )}

                                <div className="p-3">
                                    <h5 className="font-semibold text-sm text-gray-800 mb-1">
                                        {notice.title}
                                    </h5>
                                    <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                                        {notice.content}
                                    </p>

                                    <div className="flex items-center justify-between text-xs text-gray-500">
                                        <span>
                                            {new Date(notice.posted_at).toLocaleDateString('ko-KR')}
                                        </span>
                                        <div className="flex items-center space-x-3">
                                            {notice.likes && (
                                                <span>❤️ {notice.likes}</span>
                                            )}
                                            {notice.comments && (
                                                <span>💬 {notice.comments}</span>
                                            )}
                                        </div>
                                    </div>


                <a
                    href={notice.instagram_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-block text-xs text-blue-600 hover:underline"
                >
                    Instagram에서 보기 →
                </a>
                            </div>
              </div>
                ))}
            </div>
        )}
        </div>
    </div >
  );
};

export default MessageBubble;