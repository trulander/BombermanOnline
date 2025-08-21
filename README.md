# Bomberman Online
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

Multiplayer Bomberman game with online mode.

## Architecture

The project consists of the following components:

1. **Web Frontend** - client-side web application in TypeScript
2. **WebAPI Service** - FastAPI API service for handling client requests
3. **Game Service** - service for managing game logic in FastAPI
4. **Auth Service** - authentication and user management service in FastAPI
5. **AI Service** - service for managing AI units and training AI models in FastAPI
6. **Infrastructure components**:
   - PostgreSQL - database
   - Redis - caching and state storage
   - NATS - message queue for inter-service communication
   - Traefik - API Gateway and load balancer
   - Prometheus, Grafana - monitoring
   - Loki, Fluent Bit - logging

## Documentation

Here you will find detailed documentation for various components of the Bomberman Online project:

### Infrastructure

*   [Docker Compose Configuration](docs/en/infra/docker-compose.md)

### Microservices

*   [AI Service](services/ai-service/README.md)
*   [Auth Service](services/auth-service/README.md)
*   [Game Allocator Service](services/game-allocator-service/README.md)
*   [Game Service](services/game-service/README.md)
*   [Web Frontend](services/web-frontend/README.md)
*   [WebAPI Service](services/webapi-service/README.md)

## Services

### AI Service

AI Service is a component of the Bomberman Online platform responsible for managing AI units (enemies and bot players) in game sessions, as well as training artificial intelligence models. It simulates the behavior of AI-controlled entities in the game world, receives game state from `game-service`, makes decisions based on loaded models, and sends control commands back through NATS.

### Web Frontend

Frontend application written in TypeScript using:
- React + Material-UI for the user interface
- Canvas API for rendering the game field
- Axios for HTTP requests with automatic token refresh
- **REST API** for creating and managing games (instead of Socket.IO)

### WebAPI Service

REST API service for handling client requests:
- Registration and retrieval of game rooms
- Management of game sessions
- Processing WebSocket connections

### Game Service

Service for managing game logic:
- Creation and management of game sessions
- Processing game events
- Calculation of game physics and logic
- Providing a REST API for creating, managing, and retrieving information about games, teams, entities, and maps.

### Auth Service

User authentication and management service:
- User registration and authentication
- JWT token management
- OAuth 2.0 authorization via external providers
- User role management
- API protection via Traefik Forward Auth

## Routing

### User Routes

- **/** - main page with game description
- **/account/login** - login page
- **/account/register** - registration page
- **/account/reset-password** - password reset
- **/account/confirm-reset-password** - confirm password reset
- **/account/verify-email** - email verification
- **/account/dashboard** - user dashboard
- **/account/profile** - profile editing
- **/account/stats** - user game statistics
- **/account/games/create** - new game creation page
- **/account/games/:gameId/manage** - created game management page
- **/account/maps/editor** - map editor page
- **/account/game/:gameId** - game page (to join an active game)

### API Routes

- **/auth/api/v1/auth/** - authentication endpoints
- **/auth/api/v1/users/** - user management
- **/auth/api/v1/games/** - game endpoints (for game management)
- **/auth/api/v1/teams/** - team management endpoints
- **/auth/api/v1/maps/** - map management endpoints
- **/auth/api/v1/entities/** - entity information retrieval endpoints

## Security

### Authorization System
- **JWT tokens** for HTTP API and WebSocket connections
- **Refresh tokens** for automatic session renewal
- **Role-based model** (administrators, players)
- **Cookie-based authorization** for WebSocket connections

### WebSocket Authorization
The application uses **HTTP cookies** for WebSocket connection authorization:
- Upon login, a `ws_auth_token` cookie is created with path `/socket.io/`
- The cookie is automatically sent during WebSocket handshake
- Secure token transmission without using query parameters

### Routing Architecture
- **Protected routes** for authorized users (`/account/*`)
- **Public routes** for unauthorized users (`/login`, `/register`)
- **Centralized access control** via `ProtectedRoute` and `PublicRoute`

### Token Management
- **Centralized TokenService** for all token operations
- **No duplication** of logic between components
- **Automatic cookie management** for WebSocket

## Project Startup

### Requirements

- Docker and Docker Compose

### Startup

```bash
# Clone the repository
git clone https://github.com/yourusername/BombermanOnline.git
cd BombermanOnline

# Start all services (including frontend)
docker-compose up -d
```

### Accessing Services

After startup, services are available at the following addresses:

- **Game**: http://localhost/game/:gameId
- **Create Game**: http://localhost/account/games/create
- **Manage Game**: http://localhost/account/games/:gameId/manage
- **Map Editor**: http://localhost/account/maps/editor
- **User Dashboard**: http://localhost/account/dashboard
- **API**: http://localhost/api/
- **API Documentation**: http://localhost/api/docs
- **Grafana**: http://grafana.localhost/ (admin/admin)
- **Prometheus**: http://prometheus.localhost/
- **Traefik Dashboard**: http://traefik.localhost/

## Development

### Project Structure

```
BombermanOnline/
├── services/                  # Services
│   ├── ai-service/            # AI Service
│   ├── web-frontend/          # Web Frontend
│   ├── webapi-service/        # WebAPI Service
│   ├── game-service/          # Game Service
│   └── auth-service/          # Auth Service
├── infra/                     # Infrastructure
│   ├── docker-compose.yml     # Docker Compose infrastructure file
│   ├── traefik/               # Traefik Configuration
│   ├── prometheus/            # Prometheus Configuration
│   ├── grafana/               # Grafana Configuration
│   ├── loki/                  # Loki Configuration
│   └── fluent-bit/            # Fluent Bit Configuration
└── README.md                  # Documentation
└── docker-compose.yml         # Main Docker Compose file
```


## Functionality

### Game Features

- Create and join game rooms via REST API
- Manage created game sessions (start, pause, resume, delete, manage players and teams)
- Real-time multiplayer game
- Player statistics system
- User profiles with settings
- Map editor for creating and managing map templates

### Implementation Details

- Smooth camera with a "dead zone" for player tracking
- Optimized map change transmission instead of full state
- Automatic reconnection on network issues
- Logging system with server submission
- Transition from Socket.IO to REST API for game management

## User Roles

The system provides the following user roles:

1. **user** - regular user, can play games
2. **admin** - administrator, has full access to all functions
3. **moderator** - moderator, can manage game rooms and users
4. **developer** - developer, has access to technical functions

## Technologies

### Frontend
- React 18 + TypeScript
- Material-UI for interface components
- Socket.IO Client for real-time (gameplay only)
- Axios for HTTP requests with automatic token refresh
- Canvas API for game graphics

### Backend
- FastAPI for API services
- Socket.IO for WebSocket connections
- PostgreSQL for the main database
- Redis for caching and states
- NATS for inter-service communication
- `uv` for Python dependency management

### DevOps
- Docker + Docker Compose
- Traefik as API Gateway
- Prometheus + Grafana for monitoring
- Loki + Fluent Bit for logging
- Dockerfile for each service

## License