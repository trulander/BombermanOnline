# Auth Service - Bomberman Online

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

Authentication and user management service for the Bomberman Online game.

This is the main service responsible for user registration, authentication, profile management, and roles.

## Detailed Documentation

All detailed documentation on architecture, API, deployment, and configuration has been moved to the `docs/en` directory.


- [1. Service Overview](./docs/en/01_overview.md)
- [2. Technologies Used](./docs/en/02_technologies.md)
- [3. Deployment and Startup](./docs/en/03_deployment.md)
- [4. Configuration](./docs/en/04_configuration.md)
- [5. API and Frontend Endpoints](./docs/en/05_api_endpoints.md)
- [6. Database Models](./docs/en/06_database.md)
- [7. Migration Management](./docs/en/07_migrations.md)
- [8. Architecture and Logic](./docs/en/08_architecture.md)

## Secrets Management

Secrets are managed in Infisical. The `.env-example` file contains all available variables and can be imported into Infisical as a base configuration. The Docker entrypoint logs in to Infisical and runs the service with injected environment variables.

## Technologies Used

- **Python 3.12**
- **FastAPI**
- **PostgreSQL (SQLAlchemy & Alembic)**
- **Redis**
- **JWT (python-jose)**
- **OAuth 2.0**
- **Jinja2 Templates**
- **Docker**