# 6. Database Models

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/06_database.md)

The service uses PostgreSQL as its primary database. The schema is managed using SQLAlchemy and Alembic. There are two main tables: `users` and `refresh_tokens`.

## `users` Table

Stores all information about system users.

| Field                | Type                     | Description                                                              |
| -------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `id`                 | `UUID` (Primary Key)     | Unique user identifier.                                                  |
| `email`              | `String(255)` (Unique)   | User's email address.                                                    |
| `username`           | `String(50)` (Unique)    | Unique username.                                                         |
| `hashed_password`    | `String(255)` (Nullable) | Hashed password. `NULL` for users logged in via OAuth.                   |
| `full_name`          | `String(100)` (Nullable) | User's full name.                                                        |
| `profile_image`      | `String(255)` (Nullable) | URL of the profile image.                                                |
| `role`               | `String(20)`             | User's role (`user`, `admin`, `moderator`, `developer`).                 |
| `is_active`          | `Boolean`                | Flag indicating if the account is active.                                |
| `is_verified`        | `Boolean`                | Flag indicating if the email has been verified.                          |
| `is_oauth_user`      | `Boolean`                | Flag indicating if the user was created via OAuth.                       |
| `oauth_provider`     | `String(20)` (Nullable)  | Name of the OAuth provider (e.g., `google`).                             |
| `created_at`         | `DateTime(timezone=True)`| Date and time of account creation.                                       |
| `updated_at`         | `DateTime(timezone=True)`| Date and time of the last account update.                                |
| `last_login_at`      | `DateTime(timezone=True)`| Date and time of the last login.                                         |
| `verification_token` | `String(255)` (Nullable) | Token for email verification or password reset.                          |

## `refresh_tokens` Table

Stores refresh tokens used to obtain new access tokens.

| Field        | Type                     | Description                                                              |
| ------------ | ------------------------ | ------------------------------------------------------------------------ |
| `id`         | `UUID` (Primary Key)     | Unique record identifier.                                                |
| `user_id`    | `UUID` (Foreign Key)     | ID of the user who owns the token.                                       |
| `token`      | `String(255)` (Unique)   | The refresh token itself.                                                |
| `expires_at` | `DateTime(timezone=True)`| Token expiration date and time.                                          |
| `is_revoked` | `Boolean`                | Flag indicating if the token has been revoked.                           |
| `created_at` | `DateTime(timezone=True)`| Token creation date and time.                                            |
| `ip_address` | `String(45)` (Nullable)  | IP address from which the token was issued.                              |
| `user_agent` | `String(255)` (Nullable) | User-Agent of the client for which the token was issued.                 |
