# Technology Stack
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/tech_stack.md)

This document describes all the key technologies, libraries, and tools used in the `web-frontend` project.

## Core Frameworks and Libraries

*   **React (v18.2.0):** The foundation of our application. A library for building declarative and component-based user interfaces.
*   **TypeScript (v5.4.5):** A strictly typed language that compiles to JavaScript. It helps prevent errors during development and improves code readability and maintainability.
*   **React Router (v6.22.3):** A library for implementing navigation and routing in the application.

## UI and Styling

*   **Material-UI (MUI) (v5.15.12):** An extensive library of pre-built React components that implements Material Design principles. It is used to create a consistent and responsive design.
*   **Emotion (v11.11.4):** A CSS-in-JS library used by the MUI core. It allows writing CSS styles directly within components.

## Server Interaction

*   **Axios (v1.6.7):** An HTTP client for sending requests to the RESTful APIs (`Auth Service`, `WebAPI Service`). It is configured with interceptors to automatically add authorization tokens.
*   **Socket.IO Client (v4.7.4):** A client-side library for establishing and managing a WebSocket connection with the `WebAPI Service`. It is necessary for receiving real-time game state updates.

## Form Management

*   **Formik (v2.4.5):** A library for managing form state, handling submissions, and tracking errors.
*   **Yup (v1.4.0):** A library for data schema validation. It is used in conjunction with Formik to verify the correctness of user-entered data.

## Build and Development

*   **Node.js (v18-alpine):** A JavaScript runtime environment. It is used to run the development server and build the project.
*   **Webpack (v5.90.3):** A powerful module bundler. It bundles all project files (TSX, TS, CSS) into optimized bundles for browser loading.
*   **Babel (v7.24.0):** A transpiler. It converts modern JavaScript (ES6+) and TypeScript (TSX) into code compatible with most browsers.
*   **Webpack Dev Server (v5.0.2):** A server for local development that provides Hot Module Replacement to speed up the development process.

## Utilities

*   **Loglevel (v1.8.1):** A lightweight and simple library for client-side logging. It helps in debugging the application in the browser.