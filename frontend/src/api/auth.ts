const API_BASE_URL = 'http://localhost:8000/api';

export interface RegisterData {
    student_id: string;
    password: string;
    email: string;
    name: string;
    department: string;
    campus: string;
}

export interface LoginData {
    student_id: string;
    password: string;
}

export const register = async (data: RegisterData) => {
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

export const login = async (data: LoginData) => {
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

export const getProfile = async (token: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error('프로필 조회에 실패했습니다.');
    }

    return response.json();
};
