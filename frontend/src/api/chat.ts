import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ChatRequest {
    message: string;
    user_latitude?: number;
    user_longitude?: number;
}

export interface Classroom {
    id: number;
    code: string;
    building_name: string;
    building_code: string;
    room_number: string;
    floor: number;
    capacity?: number;
    description?: string;
    latitude?: number;
    longitude?: number;
    naver_place_id?: string;
}

// 🆕 Notice 타입 추가
export interface Notice {
    id: number;
    instagram_id: string;
    shortcode: string;
    title: string;
    content: string;
    instagram_url: string;
    image_url?: string;
    posted_at: string;
    crawled_at: string;
    account_name: string;
    likes?: number;
    comments?: number;
    is_active: boolean;
}

export interface ChatResponse {
    message: string;
    classroom_info?: Classroom;
    map_link?: string;
    show_map_button: boolean;
    notices?: Notice[];  // 🆕
    show_notices: boolean;  // 🆕
}

export const sendMessage = async (
    message: string,
    userLatitude?: number,
    userLongitude?: number
): Promise<ChatResponse> => {
    const response = await axios.post<ChatResponse>(`${API_BASE_URL}/api/chat`, {
        message,
        user_latitude: userLatitude,
        user_longitude: userLongitude,
    });
    return response.data;
};

export const getClassrooms = async (): Promise<Classroom[]> => {
    const response = await axios.get<Classroom[]>(`${API_BASE_URL}/api/classrooms`);
    return response.data;
};

// 🆕 공지사항 API
export const getNotices = async (limit: number = 10): Promise<Notice[]> => {
    const response = await axios.get<Notice[]>(`${API_BASE_URL}/api/notices?limit=${limit}`);
    return response.data;
};

export const searchNotices = async (query: string, limit: number = 5): Promise<Notice[]> => {
    const response = await axios.get<Notice[]>(
        `${API_BASE_URL}/api/notices/search?query=${query}&limit=${limit}`
    );
    return response.data;
};

export const syncInstagram = async (forceRefresh: boolean = false): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/api/notices/sync`, null, {
        params: { force_refresh: forceRefresh }
    });
    return response.data;
};