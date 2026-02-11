import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from app.config import settings
from app.repositories.nats_repository import NatsRepository
from app.repositories.redis_repository import RedisRepository

from app.services.grpc_server import start_grpc, stop_grpc
from app.services.grpc_client import GameServiceGRPCClient
from app.training.trainer import TrainingService
from app.inference.inference_service import InferenceService

from starlette.datastructures import State
import consul
from aioprometheus import MetricsMiddleware
from aioprometheus.asgi.starlette import metrics

logger = logging.getLogger(__name__)


def register_service():
    logger.info(f"registering in the consul service")
    service_name = settings.SERVICE_NAME
    c = consul.Consul(host=settings.CONSUL_HOST, port=8500)
    data = {
        "address": settings.HOSTNAME,  # Имя сервиса в Docker сети
        "tags": ["traefik"],
        "check": consul.Check.http(
            url=f"http://{settings.HOSTNAME}:{settings.PORT}/health",
            interval="10s",
            timeout="1s",
            deregister="60s"
        )
    }
    c.agent.service.register(
        **data,
        service_id=f"{service_name}-{settings.HOSTNAME}",
        name=f"{service_name}",
        meta={
            "rest_api_port": str(settings.PORT),
            "grpc_port": str(settings.GRPC_PORT),
        },
        port=settings.PORT
    )
    # c.agent.service.register(
    #     **data,
    #     service_id=f"{service_name}-{settings.HOSTNAME}-grpc",
    #     name=f"{service_name}-grpc",
    #     port=settings.GRPC_PORT
    # )

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

    app.state.grpc_client = GameServiceGRPCClient()
    app.state.training_service = TrainingService(
        grpc_client=app.state.grpc_client,
    )
    app.state.inference_service = InferenceService()
    app.state.grpc_server = start_grpc(
        training_service=app.state.training_service,
        inference_service=app.state.inference_service,
    )

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
    MetricsMiddleware,
)

app.add_route("/metrics", metrics)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": settings.SERVICE_NAME}
