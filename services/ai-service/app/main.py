import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from app.config import settings
from app.repositories.nats_repository import NatsRepository
from app.repositories.redis_repository import RedisRepository

from app.services.grpc_server import start_grpc, stop_grpc

from starlette.datastructures import State
import consul
import socket
from starlette_exporter import PrometheusMiddleware, handle_metrics

logger = logging.getLogger(__name__)


def register_service():
    logger.info(f"registering in the consul service")
    service_name = settings.SERVICE_NAME
    c = consul.Consul(host=settings.CONSUL_HOST, port=8500)
    service_id = f"{service_name}-{socket.gethostname()}"
    c.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=socket.gethostname(),  # Имя сервиса в Docker сети
        port=settings.PORT,
        tags=["traefik"],
        check=consul.Check.http(
            url=f"http://{socket.gethostname()}:{settings.PORT}/health",
            interval="10s",
            timeout="1s",
            deregister="60s"
        )
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ai-service")
    logger.info(f"Hostname: {settings.HOSTNAME}")
    register_service()
    
    app.state.redis_repository = RedisRepository(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )

    app.state.nats_repository = NatsRepository(
        nats_url=settings.NATS_URL
    )
    await app.state.nats_repository.aconnect()

    app.state.grpc_server = start_grpc()

    logger.info("AI Service started up.")
    yield
    # Shutdown
    logger.info("AI Service shutting down.")

    stop_grpc(app.state.grpc_server)
    if app.state.redis_repository:
        app.state.redis_repository.close()
    if app.state.nats_repository:
        await app.state.nats_repository.adisconnect()

app = FastAPI(
    title=settings.APP_TITLE,
    debug=settings.DEBUG,
    reload=settings.RELOAD,
    lifespan=lifespan
)
app.state: State

# Добавляем Prometheus метрики
app.add_middleware(
    PrometheusMiddleware,
    app_name="game_service",
    group_paths=True,
    filter_unhandled_paths=False,
)

app.add_route("/metrics", handle_metrics)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": settings.SERVICE_NAME}
