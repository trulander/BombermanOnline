# WebAPI Service
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](README_RU.md)

This document describes the **WebAPI** service for the **Bomberman Online** game. It serves as the central entry point for client applications, providing a RESTful API and WebSocket connections for real-time game interactions.

## 1. Service Purpose

The `WebAPI Service` acts as a gateway between client applications (web frontend) and internal microservices (`Game Allocator Service`, `Game Service`). Its key functions include:

*   **Providing a RESTful API**: For managing game rooms.
*   **Managing WebSocket Connections**: For exchanging real-time game events.
*   **Proxying Requests**: Redirecting HTTP requests to the appropriate `Game Service` instances.
*   **Interacting with NATS**: Asynchronous communication with other backend services.
*   **Caching**: Storing game service addresses for quick access.
*   **Metrics**: Providing metrics in Prometheus format for monitoring.

## 2. Detailed Documentation

This documentation has been expanded and divided into several files for more detailed information.

*   [**Architecture**](./docs/en/architecture.md): A detailed description of the service's internal structure.
*   [**Interaction with Other Services**](./docs/en/interactions.md): Diagrams and explanations of communications.
*   [**Use Cases**](./docs/en/use-cases.md): A step-by-step description of the main user scenarios.
*   [**API Reference**](./docs/en/api.md): A complete reference for all RESTful API and WebSocket events.
*   [**Configuration**](./docs/en/configuration.md): A guide to configuring the service.
*   [**Deployment**](./docs/en/deployment.md): Instructions for running the service.

## 3. Technologies Used

*   **FastAPI**: A web framework for creating APIs.
*   **Uvicorn**: An ASGI server.
*   **Python-SocketIO**: A library for implementing WebSockets.
*   **NATS.py**: A client for the NATS messaging system.
*   **Redis**: A repository for caching.
*   **HTTPLX**: An asynchronous HTTP client for proxying.
*   **Py-Consul**: A client for service discovery.
*   **Aioprometheus**: A toolkit for Prometheus metrics.
