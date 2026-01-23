import asyncio
import logging
import time
from typing import Any

import httpx

from ..services.nats_service import NatsService
from ..models.game import GameFilter

logger = logging.getLogger(__name__)


class GameAggregatorService:
    def __init__(self, nats_service: NatsService) -> None:
        self.nats_service = nats_service
        self._instances_cache: list[dict[str, Any]] | None = None
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 30.0

    async def _get_instances(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Получить список инстансов с кэшированием"""
        current_time = time.time()
        
        if not force_refresh and self._instances_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
            logger.debug("Using cached instances list")
            return self._instances_cache
        
        try:
            instances = await self.nats_service.get_game_service_instances()
            self._instances_cache = instances
            self._cache_timestamp = current_time
            logger.debug(f"Refreshed instances cache: {len(instances)} instances")
            return instances
        except Exception as e:
            logger.error(f"Error getting instances: {e}", exc_info=True)
            if self._instances_cache:
                logger.warning("Using stale cache due to error")
                return self._instances_cache
            return []

    async def _fetch_games_from_instance(
        self, 
        client: httpx.AsyncClient, 
        instance: dict[str, Any], 
        query_params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Получить список игр с одного инстанса"""
        try:
            address = instance["address"]
            port = instance.get("port", 5002)
            url = f"http://{address}:{port}/games/api/v1/games/"
            
            logger.debug(f"Fetching games from {address}:{port}")
            response = await client.get(url, params=query_params, timeout=10.0)
            response.raise_for_status()
            games = response.json()
            logger.debug(f"Received {len(games)} games from {address}:{port}")
            return games
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching games from {instance.get('address')}: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching games from {instance.get('address')}: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching games from {instance.get('address')}: {e}", exc_info=True)
            return []

    def _build_query_params(self, game_filter: GameFilter) -> dict[str, Any]:
        """Построить query параметры из фильтра, исключая limit и offset"""
        query_params = game_filter.model_dump(
            exclude={'limit', 'offset'}, 
            exclude_none=True,
            mode='json'
        )
        return query_params

    async def get_all_games(self, game_filter: GameFilter) -> list[dict[str, Any]]:
        """Получить список всех игр со всех инстансов"""
        instances = await self._get_instances()
        
        if not instances:
            logger.warning("No game-service instances available")
            return []
        
        query_params = self._build_query_params(game_filter=game_filter)
        logger.info(f"Fetching games from {len(instances)} instances with params: {query_params}")
        
        async with httpx.AsyncClient() as client:
            tasks = [
                self._fetch_games_from_instance(
                    client=client, 
                    instance=instance, 
                    query_params=query_params
                )
                for instance in instances
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_games = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Exception in fetch task: {result}", exc_info=True)
                    continue
                if isinstance(result, list):
                    all_games.extend(result)
            
            logger.info(f"Aggregated {len(all_games)} games from {len(instances)} instances")
            return all_games

