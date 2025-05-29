import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { User } from '../types/User';
import { LoginCredentials, RegisterData } from '../types/Auth';
import { api } from '../services/api';
import { tokenService, TokenData } from '../services/tokenService';

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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      // Проверяем наличие токенов
      if (!tokenService.hasTokens()) {
        setUser(null);
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      // Если есть токены но нет WebSocket cookie - восстанавливаем cookie
      const accessToken = tokenService.getAccessToken();
      const wsCookie = tokenService.getWebSocketAuthCookie();
      
      if (accessToken && !wsCookie) {
        console.log('Restoring WebSocket cookie from existing tokens');
        // Восстанавливаем cookie из существующих токенов
        const tokenData = {
          access_token: accessToken,
          refresh_token: tokenService.getRefreshToken() || '',
          token_type: localStorage.getItem('token_type') || 'bearer',
          expires_in: parseInt(localStorage.getItem('expires_in') || '1800')
        };
        tokenService.saveTokens(tokenData);
      }

      try {
        const response = await api.get('/users/me');
        setUser(response.data);
        setIsAuthenticated(true);
      } catch (error) {
        // Если есть refresh token, пробуем обновить токен
        if (tokenService.getRefreshToken()) {
          try {
            const tokenData = await tokenService.refreshToken();
            if (tokenData) {
              // После обновления токена, пробуем получить данные пользователя снова
              const userResponse = await api.get('/users/me');
              setUser(userResponse.data);
              setIsAuthenticated(true);
            } else {
              // Если не удалось обновить токен
              setUser(null);
              setIsAuthenticated(false);
            }
          } catch (refreshError) {
            // Если не удалось обновить токен
            tokenService.clearTokens();
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

  // Функция авторизации
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login', credentials);
      
      if (response.data) {
        // Сохраняем токены через сервис
        tokenService.saveTokens(response.data);
        
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
      
      // Очищаем токены через сервис
      tokenService.clearTokens();
      
      setUser(null);
      setIsAuthenticated(false);
      // Перенаправляем на страницу авторизации
      window.location.href = '/account/login';
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