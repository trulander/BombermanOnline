# 2. Technologies Used

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/02_technologies.md)

The service is built on a modern and high-performance technology stack, chosen to ensure reliability, scalability, and ease of development.

## Core Stack

- **Python 3.12:** The main programming language.
- **FastAPI:** A high-performance web framework for creating APIs.
- **Uvicorn:** An ASGI server for running FastAPI.

## Databases and Caching

- **PostgreSQL:** The primary relational database for storing user and token information. Used with the `asyncpg` asynchronous driver.
- **SQLAlchemy:** An ORM (Object-Relational Mapper) for interacting with PostgreSQL.
- **Alembic:** A tool for managing database schema migrations.
- **Redis:** An in-memory data store used for caching and managing the JWT token blacklist.

## Authentication and Security

- **JOSE (python-jose):** A library for creating and verifying JWT tokens.
- **Passlib & bcrypt:** Used for securely hashing and verifying passwords.
- **Pydantic:** Data validation and settings management.

## Frontend

- **Jinja2:** A template engine for generating HTML pages.
- **HTML/CSS/JS:** Standard web technologies for the user interface.

## Miscellaneous

- **UV:** A package installer and virtual environment manager.
- **Typer:** A library for creating CLI commands (used in `manage.py`).
- **Httpx:** An asynchronous HTTP client for interacting with OAuth providers.
- **Consul (py-consul):** Integration with Consul for service registration and discovery.
- **aioprometheus:** Exports metrics in Prometheus format for monitoring.
