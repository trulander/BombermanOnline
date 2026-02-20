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
        """Find one best game-service instance through game-allocator-service using load balancing"""
        try:
            subject = settings.GAME_ALLOCATOR_SERVICE_NATS_SUBJECT
            response = self.nats_repository.request(
                subject=subject,
                data={"resource_type": "cpu"},
                timeout=5.0
            )
            if response and response.get("success") and response.get("instance"):
                instance = response.get("instance")
                logger.info(f"Found game-service instance: {instance}")
                return instance
            logger.warning(f"No game-service instances available: {response.get('message', 'Unknown error') if response else 'No response'}")
            return None
        except Exception as e:
            logger.error(f"Error finding game-service instance: {e}", exc_info=True)
            return None



