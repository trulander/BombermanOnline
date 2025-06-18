import axios from 'axios';

const createAxiosInstance = (baseURL: string) => {
  const instance = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });

  // Добавляем перехватчик запросов для добавления токена авторизации
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Добавляем перехватчик ответов для обработки ошибок авторизации и обновления токена
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      // Если ошибка 401 и запрос не был повторен
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          // Пробуем обновить токен
          const refreshToken = localStorage.getItem('refresh_token');
          if (!refreshToken) {
            throw new Error('Refresh token not found');
          }
          
          const response = await axios.post('/auth/api/v1/auth/refresh', { // Используем полный путь для refresh, т.к. это всегда auth-service
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token, token_type, expires_in } = response.data;
          
          // Сохраняем новые токены
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          localStorage.setItem('token_type', token_type || 'bearer');
          localStorage.setItem('expires_in', expires_in?.toString() || '1800');
          localStorage.setItem('token_time', Date.now().toString());
          
          // Повторяем исходный запрос с новым токеном
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // Если не удалось обновить токен, очищаем localStorage
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token_type');
          localStorage.removeItem('expires_in');
          localStorage.removeItem('token_time');
          
          // Перенаправляем на страницу авторизации
          window.location.href = '/account/login';
          return Promise.reject(refreshError);
        }
      }
      
      return Promise.reject(error);
    }
  );
  return instance;
};

export const authApi = createAxiosInstance('/auth/api/v1');
export const gameApi = createAxiosInstance('/games/api/v1');
export const webApi = createAxiosInstance('/webapi/api/v1'); 