import logging
from typing import Optional

from ..config import settings
from ..repositories.nats_repository import NatsRepository

logger = logging.getLogger(__name__)


class GameServiceFinder:
    """Service for finding game-service instances through game-allocator-service"""
    
    def __init__(self, nats_repository: NatsRepository):
        self.nats_repository = nats_repository

    def find_game_service_instance(self) -> Optional[dict]:
        """Find available game-service instance through game-allocator-service"""
        try:
            subject = settings.GAME_ALLOCATOR_SERVICE_NATS_SUBJECT
            response = self.nats_repository.request(subject=subject, data={}, timeout=5.0)
            if response.get("success") and response.get("instances"):
                instances: list = response["instances"]
                if instances:
                    instance = instances[0]
                    logger.info(f"Found game-service instance: {instance}")
                    return instance
            logger.warning("No game-service instances available")
            return None
        except Exception as e:
            logger.error(f"Error finding game-service instance: {e}", exc_info=True)
            return None
