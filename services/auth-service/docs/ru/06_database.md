# 6. Модели Базы Данных

[![English](https://img.shields.io/badge/lang-English-blue)](../en/06_database.md)

Сервис использует PostgreSQL в качестве основной базы данных. Схема управляется с помощью SQLAlchemy и Alembic. Существуют две основные таблицы: `users` и `refresh_tokens`.

## Таблица `users`

Хранит всю информацию о пользователях системы.

| Поле                 | Тип                      | Описание                                                                 |
| -------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `id`                 | `UUID` (Primary Key)     | Уникальный идентификатор пользователя.                                   |
| `email`              | `String(255)` (Unique)   | Адрес электронной почты пользователя.                                    |
| `username`           | `String(50)` (Unique)    | Уникальное имя пользователя.                                             |
| `hashed_password`    | `String(255)` (Nullable) | Хэшированный пароль. `NULL` для пользователей, вошедших через OAuth.    |
| `full_name`          | `String(100)` (Nullable) | Полное имя пользователя.                                                 |
| `profile_image`      | `String(255)` (Nullable) | URL изображения профиля.                                                 |
| `role`               | `String(20)`             | Роль пользователя (`user`, `admin`, `moderator`, `developer`).           |
| `is_active`          | `Boolean`                | Флаг, указывающий, активен ли аккаунт.                                   |
| `is_verified`        | `Boolean`                | Флаг, подтверждена ли электронная почта.                                 |
| `is_oauth_user`      | `Boolean`                | Флаг, был ли пользователь создан через OAuth.                            |
| `oauth_provider`     | `String(20)` (Nullable)  | Название OAuth-провайдера (например, `google`).                          |
| `created_at`         | `DateTime(timezone=True)`| Дата и время создания аккаунта.                                          |
| `updated_at`         | `DateTime(timezone=True)`| Дата и время последнего обновления аккаунта.                             |
| `last_login_at`      | `DateTime(timezone=True)`| Дата и время последнего входа.                                           |
| `verification_token` | `String(255)` (Nullable) | Токен для подтверждения email или сброса пароля.                         |

## Таблица `refresh_tokens`

Хранит refresh-токены, используемые для получения новых access-токенов.

| Поле         | Тип                      | Описание                                                                 |
| ------------ | ------------------------ | ------------------------------------------------------------------------ |
| `id`         | `UUID` (Primary Key)     | Уникальный идентификатор записи.                                         |
| `user_id`    | `UUID` (Foreign Key)     | ID пользователя, которому принадлежит токен.                             |
| `token`      | `String(255)` (Unique)   | Сам refresh-токен.                                                       |
| `expires_at` | `DateTime(timezone=True)`| Дата и время истечения срока действия токена.                            |
| `is_revoked` | `Boolean`                | Флаг, отозван ли токен.                                                  |
| `created_at` | `DateTime(timezone=True)`| Дата и время создания токена.                                            |
| `ip_address` | `String(45)` (Nullable)  | IP-адрес, с которого был выпущен токен.                                  |
| `user_agent` | `String(255)` (Nullable) | User-Agent клиента, для которого был выпущен токен.                      |