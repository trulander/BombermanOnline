# WebAPI Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

This document describes the **WebAPI** service for the **Bomberman Online** game. It serves as a central entry point for client applications, providing RESTful API and WebSocket connections for real-time game interactions.

## 1. Service Purpose

`WebAPI Service` acts as a gateway between client applications (web frontend) and internal microservices (`Game Allocator Service`, `Game Service`). Its key functions include:

*   **Providing RESTful API**: For managing game rooms.
*   **Managing WebSocket connections**: For exchanging real-time game events.
*   **Request Proxying**: Redirecting HTTP requests to appropriate `Game Service` instances.
*   **NATS Interaction**: Asynchronous communication with other backend services.
*   **Caching**: Storing game service addresses for quick access.
*   **Metrics**: Providing metrics in Prometheus format for monitoring.

## 2. Detailed Documentation

This documentation has been expanded and divided into several files for more detailed study.

*   [**Architecture**](./docs/en/architecture.md): Detailed description of the service's internal structure.
*   [**Interaction with Other Services**](./docs/en/interactions.md): Diagrams and explanations of communications.
*   [**Use Cases**](./docs/en/use-cases.md): Step-by-step description of main user scenarios.
*   [**API Description**](./docs/en/api.md): Full reference for all RESTful API and WebSocket events.
*   [**Configuration**](./docs/en/configuration.md): Guide to configuring the service.
*   [**Deployment**](./docs/en/deployment.md): Instructions for running the service.

## 3. Technologies Used

*   **FastAPI**: Web framework for building APIs.
*   **Uvicorn**: ASGI server.
*   **Python-SocketIO**: Library for WebSocket implementation.
*   **NATS.py**: Client for the NATS messaging system.
*   **Redis**: Storage for caching.
*   **HTTPLX**: Asynchronous HTTP client for proxying.
*   **Py-Consul**: Client for service discovery.
*   **Aioprometheus**: Prometheus metrics instrumentation.