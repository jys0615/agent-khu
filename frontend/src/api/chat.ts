const API_BASE_URL = 'http://localhost:8000/api';

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
