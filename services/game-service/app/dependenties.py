from app.coordinators.game_coordinator import GameCoordinator
from app.coordinators.training_coordinator import TrainingCoordinator
from app.repositories.map_repository import MapRepository
from app.repositories.nats_repository import NatsRepository
from app.repositories.postgres_repository import PostgresRepository
from app.repositories.redis_repository import RedisRepository
from app.services.event_service import EventService
from app.services.ai_inference_service import AIInferenceService
from app.config import settings

# Глобальные переменные для сервисов

# Глобальный экземпляр репозитория


nats_repository = NatsRepository()
redis_repository = RedisRepository()
postgres_repository = PostgresRepository()
map_repository = MapRepository(redis_repository=redis_repository, postgres_repository=postgres_repository)
event_service = EventService(nats_repository=nats_repository)
ai_inference_service = AIInferenceService(
    event_service=event_service
)
game_coordinator = GameCoordinator(
    notification_service=event_service,
    map_repository=map_repository,
    ai_inference_service=ai_inference_service,
)
training_coordinator = TrainingCoordinator(
    map_repository=map_repository,
)
