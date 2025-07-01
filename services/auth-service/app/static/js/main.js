// Функция для отправки данных формы на сервер в формате JSON
async function submitForm(form, url, method = 'POST') {
    // Предотвращаем стандартное поведение формы
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Собираем данные формы в объект
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        try {
            // Отправляем запрос на сервер
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'include', // Включаем отправку cookie
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Ошибка запроса');
            }
            
            // Токены уже сохранены в cookie на сервере, перенаправляем на дашборд
            if (url.includes('/auth/login') || result.access_token) {
                window.location.href = '/ui/dashboard';
            } else if (result.message) {
                // Если в ответе есть сообщение, отображаем его
                showMessage(result.message, 'success');
            }
            
            return result;
        } catch (error) {
            // Отображаем ошибку
            showMessage(error.message, 'error');
            console.error('Error:', error);
            return null;
        }
    });
}

// Функция для отображения сообщений
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'info')}`;
    alertDiv.textContent = message;
    
    // Находим контейнер и добавляем сообщение в начало
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Убираем сообщение через 5 секунд
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Функция для получения данных с API
async function fetchAPI(url, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Accept': 'application/json'
            },
            credentials: 'include'  // Включаем отправку cookie
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            // Если ошибка 401, перенаправляем на страницу входа
            window.location.href = '/ui/login';
            return null;
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка запроса');
        }
        
        // Если ответ пустой, возвращаем true
        if (response.status === 204) {
            return true;
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showMessage(error.message, 'error');
        return null;
    }
}

// Функция для обновления токена
async function refreshToken() {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
            return false;
        }
        
        const response = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (!response.ok) {
            // Если не удалось обновить токен, очищаем localStorage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('expires_in');
            localStorage.removeItem('token_time');
            return false;
        }
        
        const result = await response.json();
        
        // Сохраняем новые токены
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('refresh_token', result.refresh_token);
        localStorage.setItem('token_type', result.token_type || 'bearer');
        localStorage.setItem('expires_in', result.expires_in || 1800);
        localStorage.setItem('token_time', Date.now());
        
        return true;
    } catch (error) {
        console.error('Refresh Token Error:', error);
        return false;
    }
}

// Функция выхода из системы
async function logout() {
    try {
        await fetch('/api/v1/auth/logout', {
            method: 'POST',
            credentials: 'include',  // Включаем отправку cookie
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Перенаправляем на страницу входа
        window.location.href = '/ui/login';
    } catch (error) {
        console.error('Logout Error:', error);
    }
}

// Функция для проверки авторизации при загрузке страницы
function checkAuth() {
    // Получаем токен из localStorage
    const token = localStorage.getItem('access_token');
    const tokenTime = localStorage.getItem('token_time');
    const expiresIn = localStorage.getItem('expires_in');
    
    if (!token || !tokenTime || !expiresIn) {
        return false;
    }
    
    // Проверяем не истек ли срок действия токена
    const now = Date.now();
    const tokenAge = now - parseInt(tokenTime);
    const expiresInMs = parseInt(expiresIn) * 1000;
    
    if (tokenAge >= expiresInMs) {
        // Если токен устарел, пытаемся обновить его
        refreshToken().then(refreshed => {
            if (!refreshed) {
                // Если не удалось обновить токен, перенаправляем на страницу входа
                window.location.href = '/ui/login';
            }
        });
    }
    
    return true;
}

// Функция для обновления данных пользователя
async function updateUserProfile(data) {
    return await fetchAPI('/api/v1/users/me', 'PUT', data);
}

// Функция для получения данных пользователя
async function getUserProfile() {
    return await fetchAPI('/api/v1/users/me');
}

// Добавляем обработчики событий при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем авторизацию
    const isAuth = checkAuth();
    
    // Обработчик для формы входа
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        submitForm(loginForm, '/api/v1/auth/login');
    }
    
    // Обработчик для формы регистрации
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        submitForm(registerForm, '/api/v1/users');
    }
    
    // Обработчик для формы сброса пароля
    const resetPasswordForm = document.getElementById('reset-password-form');
    if (resetPasswordForm) {
        submitForm(resetPasswordForm, '/api/v1/auth/reset-password');
    }
    
    // Обработчик для формы подтверждения сброса пароля
    const confirmResetForm = document.getElementById('confirm-reset-form');
    if (confirmResetForm) {
        submitForm(confirmResetForm, '/api/v1/auth/confirm-reset-password');
    }
    
    // Обработчик для формы редактирования профиля
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        submitForm(profileForm, '/api/v1/users/me', 'PUT');
    }
    
    // Обработчик для кнопки выхода
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
}); 