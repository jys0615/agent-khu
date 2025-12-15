const API_BASE_URL = 'http://localhost:8000/api';

export interface User {
    id: number;
    student_id: string;
    name?: string;
    department: string;
    campus: string;
    admission_year: number;
    is_transfer: boolean;
    transfer_year?: number | null;
    current_grade?: number | null;
    interests?: string[];
    completed_credits?: number | null;
    double_major?: string | null;
    minor?: string | null;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface RegisterData {
    student_id: string;
    password: string;
    email: string;
    name: string;
    department: string;
    campus: string;
    admission_year?: number;
    is_transfer?: boolean;
    transfer_year?: number;
    double_major?: string;
    minor?: string;
}

export interface LoginData {
    student_id: string;
    password: string;
}

export interface ProfileUpdateData {
    name?: string;
    student_id?: string;
    admission_year?: number;
    campus?: string;
    is_transfer?: boolean;
    transfer_year?: number;
    double_major?: string;
    minor?: string;
}

export const register = async (data: RegisterData): Promise<TokenResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '회원가입에 실패했습니다.');
    }

    return response.json();
};

export const login = async (data: LoginData): Promise<TokenResponse> => {
    // OAuth2PasswordRequestForm 형식으로 전송 (form-data)
    const formData = new URLSearchParams();
    formData.append('username', data.student_id);  // username으로 전송
    formData.append('password', data.password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '로그인에 실패했습니다.');
    }

    return response.json();
};

export const getProfile = async (token: string): Promise<User> => {
    const response = await fetch(`${API_BASE_URL}/profiles/me`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error('프로필 조회에 실패했습니다.');
    }

    return response.json();
};

export const updateProfile = async (token: string, data: ProfileUpdateData): Promise<User> => {
    const response = await fetch(`${API_BASE_URL}/profiles/me`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || '프로필 수정에 실패했습니다.');
    }

    return response.json();
};
