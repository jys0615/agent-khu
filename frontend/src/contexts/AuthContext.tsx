import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
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

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, user: User) => void;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // 로컬스토리지에서 토큰 불러오기
        const savedToken = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');
        
        if (savedToken && savedUser) {
            setToken(savedToken);
            setUser(JSON.parse(savedUser));
        }

        setIsLoading(false);
    }, []);

    const login = (newToken: string, newUser: User) => {
        const normalizedUser: User = {
            ...newUser,
            interests: newUser.interests ?? [],
            completed_credits: newUser.completed_credits ?? 0,
        };
        setToken(newToken);
        setUser(normalizedUser);
        localStorage.setItem('token', newToken);
        localStorage.setItem('user', JSON.stringify(normalizedUser));
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    };

    return (
        <AuthContext.Provider value={{
            user,
            token,
            login,
            logout,
            isAuthenticated: !!token,
            isLoading,
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
