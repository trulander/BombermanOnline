# 5. API and Frontend Endpoints

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/05_api_endpoints.md)

The service provides both a RESTful API for programmatic interaction and a web interface for users.

## Service Endpoints

- `GET /`: Root route. Redirects to `/ui/login`.
- `GET /health`: Service health check. Returns `{"status": "healthy"}`.
- `GET /ping`: Simple ping to check availability. Returns `pong`.
- `GET /metrics`: Exports metrics in Prometheus format.

## API Endpoints (`/auth/api/v1`)

### Authentication

- `POST /auth/login`: System login.
  - **Request Body:** `LoginForm` (`username`, `password`, `remember_me`)
  - **Response:** `Token` (access_token, refresh_token, etc.)
- `POST /auth/refresh`: Token refresh.
  - **Request Body:** `RefreshTokenRequest` (`refresh_token`)
  - **Response:** `Token`
- `POST /auth/logout`: System logout (adds the current token to the blacklist).
  - **Requires:** `Authorization: Bearer <token>` header
- `GET /auth/check`: Token verification (for Traefik Forward Auth).
  - **Parameters:** `redirect: bool` (if `true`, redirects to `/ui/login` on error).
  - **Requires:** `Authorization: Bearer <token>` header
  - **Response:** `200 OK` with `X-User-ID`, `X-User-Role`, etc. headers on success, or `401 Unauthorized` on failure.

### Access Recovery

- `POST /auth/reset-password`: Request a password reset.
  - **Request Body:** `PasswordResetRequest` (`email`)
- `POST /auth/confirm-reset-password`: Confirm password reset.
  - **Request Body:** `PasswordReset` (`token`, `new_password`)
- `GET /auth/verify-email`: Verify email via token.
  - **Parameters:** `token: str`

### OAuth 2.0

- `GET /auth/oauth/{provider}`: Start OAuth authorization (e.g., `/auth/oauth/google`).
  - **Response:** JSON with `authorize_url` for redirection.
- `GET /auth/oauth/{provider}/callback`: OAuth authorization callback.
  - **Parameters:** `code`, `state`
  - **Response:** JSON with tokens and user information.

### Users

- `POST /users`: Create a new user (registration).
  - **Request Body:** `UserCreate`
  - **Response:** `UserResponse`
- `GET /users/me`: Get information about the current user.
  - **Requires:** `Authorization`
  - **Response:** `UserResponse`
- `PUT /users/me`: Update information for the current user.
  - **Requires:** `Authorization`
  - **Request Body:** `UserUpdate`
  - **Response:** `UserResponse`
- `GET /users`: Search for users.
  - **Requires:** `Authorization`
  - **Parameters:** `query`, `page`, `size`
  - **Response:** `UserSearchResponse`
- `GET /users/{user_id}`: Get user information by ID.
  - **Requires:** `Authorization`
  - **Response:** `UserResponse`
- `PUT /users/{user_id}/role`: Update a user's role (administrators only).
  - **Requires:** `Authorization` (with `admin` rights)
  - **Request Body:** `role: str`
  - **Response:** `UserResponse`

## Frontend Endpoints (`/ui`)

These routes return HTML pages.

- `GET /login`: Login page.
- `GET /register`: Registration page.
- `GET /reset-password`: Password reset request page.
- `GET /confirm-reset-password`: Page to enter a new password (requires `token` in parameters).
- `GET /verify-email`: Page to verify email (requires `token` in parameters).
- `GET /dashboard`: User dashboard (requires authorization).
- `GET /profile`: User profile page (requires authorization).
