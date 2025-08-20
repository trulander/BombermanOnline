# 5. API и Frontend Эндпоинты

Сервис предоставляет как RESTful API для программного взаимодействия, так и веб-интерфейс для пользователей.

## Служебные эндпоинты

- `GET /`: Корневой маршрут. Перенаправляет на `/ui/login`.
- `GET /health`: Проверка работоспособности сервиса. Возвращает `{"status": "healthy"}`.
- `GET /ping`: Простой пинг для проверки доступности. Возвращает `pong`.
- `GET /metrics`: Экспорт метрик в формате Prometheus.

## API Endpoints (`/auth/api/v1`)

### Аутентификация

- `POST /auth/login`: Вход в систему.
  - **Тело запроса:** `LoginForm` (`username`, `password`, `remember_me`)
  - **Ответ:** `Token` (access_token, refresh_token, etc.)
- `POST /auth/refresh`: Обновление токена.
  - **Тело запроса:** `RefreshTokenRequest` (`refresh_token`)
  - **Ответ:** `Token`
- `POST /auth/logout`: Выход из системы (добавляет текущий токен в черный список).
  - **Требуется:** Заголовок `Authorization: Bearer <token>`
- `GET /auth/check`: Проверка токена (для Traefik Forward Auth).
  - **Параметры:** `redirect: bool` (если `true`, перенаправляет на `/ui/login` при ошибке).
  - **Требуется:** Заголовок `Authorization: Bearer <token>`
  - **Ответ:** `200 OK` с заголовками `X-User-ID`, `X-User-Role` и др. при успехе, или `401 Unauthorized` при ошибке.

### Восстановление доступа

- `POST /auth/reset-password`: Запрос на сброс пароля.
  - **Тело запроса:** `PasswordResetRequest` (`email`)
- `POST /auth/confirm-reset-password`: Подтверждение сброса пароля.
  - **Тело запроса:** `PasswordReset` (`token`, `new_password`)
- `GET /auth/verify-email`: Подтверждение email по токену.
  - **Параметры:** `token: str`

### OAuth 2.0

- `GET /auth/oauth/{provider}`: Начало OAuth авторизации (например, `/auth/oauth/google`).
  - **Ответ:** JSON с `authorize_url` для редиректа.
- `GET /auth/oauth/{provider}/callback`: Callback OAuth авторизации.
  - **Параметры:** `code`, `state`
  - **Ответ:** JSON с токенами и информацией о пользователе.

### Пользователи

- `POST /users`: Создание нового пользователя (регистрация).
  - **Тело запроса:** `UserCreate`
  - **Ответ:** `UserResponse`
- `GET /users/me`: Получение информации о текущем пользователе.
  - **Требуется:** `Authorization`
  - **Ответ:** `UserResponse`
- `PUT /users/me`: Обновление информации о текущем пользователе.
  - **Требуется:** `Authorization`
  - **Тело запроса:** `UserUpdate`
  - **Ответ:** `UserResponse`
- `GET /users`: Поиск пользователей.
  - **Требуется:** `Authorization`
  - **Параметры:** `query`, `page`, `size`
  - **Ответ:** `UserSearchResponse`
- `GET /users/{user_id}`: Получение информации о пользователе по ID.
  - **Требуется:** `Authorization`
  - **Ответ:** `UserResponse`
- `PUT /users/{user_id}/role`: Обновление роли пользователя (только для администраторов).
  - **Требуется:** `Authorization` (с правами `admin`)
  - **Тело запроса:** `role: str`
  - **Ответ:** `UserResponse`

## Frontend Endpoints (`/ui`)

Эти маршруты возвращают HTML-страницы.

- `GET /login`: Страница входа.
- `GET /register`: Страница регистрации.
- `GET /reset-password`: Страница запроса на сброс пароля.
- `GET /confirm-reset-password`: Страница для ввода нового пароля (требует `token` в параметрах).
- `GET /verify-email`: Страница для подтверждения email (требует `token` в параметрах).
- `GET /dashboard`: Личный кабинет пользователя (требует авторизации).
- `GET /profile`: Страница профиля пользователя (требует авторизации).
