import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from app.config import settings
from app.registry.ai_agent_registry import AIAgentRegistry
from app.repositories.nats_repository import NatsRepository
from app.repositories.redis_repository import RedisRepository
from app.training.model_manager import ModelManager
from app.training.trainer import Trainer
from app.nats_controller import NATSController
from app.entities.game_state_representation import TrainingRequest
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
            timeout="1s"
        )
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ai-service")
    logger.info(f"Hostname: {settings.HOSTNAME}")
    register_service()
    nats_repository = NatsRepository(settings.NATS_URL)
    await nats_repository.connect()
    app.state.nats_repository = nats_repository
    app.state.redis_repository = RedisRepository(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD
    )
    app.state.model_manager = ModelManager(models_base_path=settings.MODELS_PATH)
    app.state.trainer = Trainer(nats_repository=nats_repository, model_manager=app.state.model_manager, logs_path=settings.LOGS_PATH)
    app.state.nats_controller = NATSController(nats_repository=nats_repository)
    app.state.ai_agent_registry = AIAgentRegistry(nats_controller=app.state.nats_controller, model_manager=app.state.model_manager)

    # Subscribe to entity spawn/despawn events from Game Service
    await app.state.nats_repository.subscribe("ai.entity_spawn", app.state.ai_agent_registry.handle_entity_spawn)
    await app.state.nats_repository.subscribe("ai.entity_despawn", app.state.ai_agent_registry.handle_entity_despawn)

    logger.info("AI Service started up.")
    yield
    # Shutdown
    logger.info("AI Service shutting down.")
    if app.state.nats_repository:
        await app.state.nats_repository.disconnect()
    if app.state.redis_repository:
        await app.state.redis_repository.close()

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


@app.post("/train")
async def start_training(request: TrainingRequest) -> Dict[str, str]:
    logger.info(f"Received training request: {request.game_id}")
    # Run training in a separate task so it doesn't block the API
    asyncio.create_task(app.state.trainer.train(
        game_id=request.game_id,
        player_id=request.player_id,
        game_mode=request.game_mode,
        total_timesteps=request.total_timesteps,
        save_interval=request.save_interval,
        algorithm_name=request.algorithm_name,
        continue_training=request.continue_training
    ))
    return {"message": f"Training started for game {request.game_id} and mode {request.game_mode}."} 