import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { User } from '../types/User';
import { LoginCredentials, RegisterData } from '../types/Auth';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<boolean>;
  confirmResetPassword: (token: string, newPassword: string) => Promise<boolean>;
  updateProfile: (data: Partial<User>) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  // Проверка авторизации при загрузке приложения
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Получаем данные пользователя
        const response = await api.get('/users/me');
        setUser(response.data);
        setIsAuthenticated(true);
      } catch (error) {
        // Если есть refresh token, пробуем обновить токен
        const refreshToken_storage = localStorage.getItem('refresh_token');
        if (refreshToken_storage) {
          try {
            await refreshToken();
            // После обновления токена, пробуем получить данные пользователя снова
            const userResponse = await api.get('/users/me');
            setUser(userResponse.data);
            setIsAuthenticated(true);
          } catch (refreshError) {
            // Если не удалось обновить токен, очищаем localStorage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('expires_in');
            localStorage.removeItem('token_time');
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Функция обновления токена
  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        return false;
      }
      
      const response = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      });
      
      if (response.data) {
        // Сохраняем новые токены
        const { access_token, refresh_token, token_type, expires_in } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('token_type', token_type || 'bearer');
        localStorage.setItem('expires_in', expires_in?.toString() || '1800');
        localStorage.setItem('token_time', Date.now().toString());
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка обновления токена:', error);
      return false;
    }
  };

  // Функция авторизации
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login', credentials);
      
      if (response.data) {
        const { access_token, refresh_token, token_type, expires_in } = response.data;
        
        // Сохраняем токены
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('token_type', token_type || 'bearer');
        localStorage.setItem('expires_in', expires_in?.toString() || '1800');
        localStorage.setItem('token_time', Date.now().toString());
        
        // Получаем данные пользователя
        const userResponse = await api.get('/users/me');
        setUser(userResponse.data);
        setIsAuthenticated(true);
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка авторизации:', error);
      return false;
    }
  };

  // Функция регистрации
  const register = async (data: RegisterData): Promise<boolean> => {
    try {
      const response = await api.post('/users', data);
      
      if (response.data) {
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      return false;
    }
  };

  // Функция выхода из системы
  const logout = async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
      
      // Очищаем localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('expires_in');
      localStorage.removeItem('token_time');
      
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Ошибка выхода из системы:', error);
    }
  };

  // Функция сброса пароля
  const resetPassword = async (email: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/reset-password', { email });
      
      if (response.data) {
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка сброса пароля:', error);
      return false;
    }
  };

  // Функция подтверждения сброса пароля
  const confirmResetPassword = async (token: string, new_password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/confirm-reset-password', {
        token,
        new_password
      });
      
      if (response.data) {
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка подтверждения сброса пароля:', error);
      return false;
    }
  };

  // Функция обновления профиля
  const updateProfile = async (data: Partial<User>): Promise<boolean> => {
    try {
      const response = await api.put('/users/me', data);
      
      if (response.data) {
        setUser(response.data);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Ошибка обновления профиля:', error);
      return false;
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
    resetPassword,
    confirmResetPassword,
    updateProfile
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 