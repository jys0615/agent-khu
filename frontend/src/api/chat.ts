import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ChatRequest {
    message: string;
    user_latitude?: number;
    user_longitude?: number;
    library_username?: string;  // 🆕 도서관 학번
    library_password?: string;  // 🆕 도서관 비밀번호
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

export interface RequirementGroup {
    key: string;
    name?: string;
    min_credits: number;
    required_courses?: string[];
    any_of?: string[][];
}

export interface Requirements {
    program: string;        // e.g., KHU-CSE
    year: string;           // e.g., "2025"
    total_credits?: number;
    groups: RequirementGroup[];
    policies?: {
        english_major_courses_required?: number;
        [k: string]: any;
    };
    notes?: string;
}

export interface Evaluation {
    program: string;
    year: string;
    ok: boolean;
    groups: Array<{
        group: string;
        min_credits: number;
        earned_credits: number;
        missing_required: string[];
        any_of?: Array<{ options: string[]; ok: boolean }>;
        ok: boolean;
    }>;
    totals?: {
        required_credits_sum?: number;
        earned_credits_sum?: number;
    };
    policies?: {
        english_required?: number;
        english_earned?: number;
        english_ok?: boolean;
    };
    evaluated_at?: string;
}

// 🆕 도서관 타입 추가
export interface LibraryInfo {
    name: string;
    campus: string;
    address: string;
    phone: string;
    hours: {
        weekday: string;
        weekend: string;
    };
    floors: Array<{
        name: string;
        total_seats: number;
        hours: string;
    }>;
}

export interface LibrarySeats {
    campus: string;
    library: string;
    total_seats: number;
    occupied: number;
    available: number;
    occupancy_rate: number;
    floors: Array<{
        name: string;
        total: number;
        occupied: number;
        available: number;
        occupancy_rate?: number;
        hours?: string;
    }>;
    updated_at?: string;
}

export interface ChatResponse {
    message: string;

    // 기존 필드들
    classroom_info?: Classroom;
    map_link?: string;
    show_map_button: boolean;
    notices?: Notice[];
    show_notices: boolean;

    // 🆕 교과과정 표시용
    requirements?: Requirements;
    show_requirements?: boolean;
    evaluation?: Evaluation;
    show_evaluation?: boolean;

    // 🆕 도서관 필드 추가
    library_info?: LibraryInfo;
    show_library_info?: boolean;
    library_seats?: LibrarySeats;
    show_library_seats?: boolean;
    reservation?: any;
    show_reservation?: boolean;

    // 🆕 로그인 필요 여부
    needs_library_login?: boolean;

    // (옵션) 과목 검색 결과가 여기에 담겨오면 같이 렌더 가능
    curriculum_courses?: Array<any>;
}


export const sendMessage = async (
    message: string,
    latitude?: number,
    longitude?: number,
    libraryUsername?: string,
    libraryPassword?: string
) => {
    const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message,
        latitude,
        longitude,
        library_username: libraryUsername,
        library_password: libraryPassword
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