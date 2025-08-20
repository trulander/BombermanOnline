# 1. Authorization Service Overview

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/01_overview.md)

The authorization and user management service is a key component of the "Bomberman Online" platform. It is responsible for all aspects related to user identification, authentication, and data management.

## Key Features

- **Registration and Authentication:** Standard registration via email/password and subsequent login.
- **Profile Management:** Users can view and update their profile information.
- **Security:** Uses modern password hashing methods (bcrypt) and JWT (JSON Web Tokens) to secure sessions.
- **OAuth 2.0:** Integration with external providers (Google) for simplified registration and login.
- **Role Management:** A flexible role system (`user`, `admin`, `moderator`, `developer`) to control access to various application functions.
- **Password Reset and Email Verification:** Mechanisms for recovering access and confirming email authenticity.
- **Traefik Integration:** The service can work with Traefik Forward Auth for centralized protection of routes throughout the infrastructure.
- **Web Interface:** A simple and clear user interface for all main functions (login, registration, dashboard).
