const API_BASE_URL = `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api`;

export type StreamEvent =
    | { type: 'connected'; session_id: string }
    | { type: 'text'; delta: string }
    | { type: 'tool_start'; tool: string; label: string }
    | { type: 'tool_end'; tool: string }
    | { type: 'done'; result: Record<string, unknown> }
    | { type: 'error'; message: string };

export const sendMessageStream = async (
    message: string,
    onEvent: (event: StreamEvent) => void,
    latitude?: number,
    longitude?: number,
    libraryUsername?: string,
    libraryPassword?: string,
): Promise<void> => {
    const token = localStorage.getItem('token');

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
            message,
            latitude,
            longitude,
            library_username: libraryUsername,
            library_password: libraryPassword,
        }),
    });

    if (!response.ok || !response.body) {
        throw new Error('스트리밍 연결에 실패했습니다.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() ?? '';

        for (const chunk of lines) {
            const line = chunk.trim();
            if (!line.startsWith('data: ')) continue;
            try {
                const event = JSON.parse(line.slice(6)) as StreamEvent;
                onEvent(event);
            } catch {
                // 파싱 실패 무시
            }
        }
    }
};

export const sendMessage = async (
    message: string,
    latitude?: number,
    longitude?: number,
    libraryUsername?: string,
    libraryPassword?: string
) => {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
            message,
            latitude,
            longitude,
            library_username: libraryUsername,
            library_password: libraryPassword,
        }),
    });

    if (!response.ok) {
        throw new Error('메시지 전송에 실패했습니다.');
    }

    return response.json();
};
