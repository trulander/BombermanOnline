import logging
from enum import Enum
from typing import Callable, Any

import asyncio
import json
import consul
from prometheus_api_client import PrometheusConnect

from config import settings
from logging_config import configure_logging
from nats_repository import NatsRepository
from game_cache import GameInstanceCache
from redis_repository import RedisRepository
from nats.aio.msg import Msg


logger = logging.getLogger(__name__)

class NatsEvents(Enum):
    GAME_ID_ASSIGN_GAME_SERVER = "game.assign.request"


class GameAllocatorService:
    def __init__(self):
        self.nats_repository = NatsRepository()
        self.redis_repository = RedisRepository()
        self.consul = consul.Consul(host=settings.CONSUL_HOST, port=8500)
        self.prom = PrometheusConnect(url=settings.PROMETHEUS_URL, disable_ssl=True)
        self.cache = GameInstanceCache(redis_repository=self.redis_repository, ttl=settings.GAME_CACHE_TTL)

    # def subscribe_events(self):

    def get_instance_load(self, instance_id, address):
        logger.debug(f"get_instance_load - instance_id:{instance_id}, address:{address}")
        # CPU usage (PromQL)
        cpu_query = f'rate(container_cpu_usage_seconds_total{{container_label_com_docker_compose_service="game-service", instance=~".*{address}.*"}}[5m])'
        cpu_result = self.prom.custom_query(cpu_query)
        cpu_usage = float(cpu_result[0]["value"][1]) if cpu_result else 0.0

        # RAM usage
        ram_query = f'container_memory_usage_bytes{{container_label_com_docker_compose_service="game-service", instance=~".*{address}.*"}}'
        ram_result = self.prom.custom_query(ram_query)
        ram_usage = float(ram_result[0]["value"][1]) if ram_result else 0.0

        result = {
            "instance_id": instance_id,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "address": address
        }
        logger.debug(f"get_instance_load - result:{result}")
        return result

    async def assign_game_instance(self, game_id: str, game_settings: dict):
        logger.debug(f"assign_game_instance - game_id:{game_id}, game_settings:{game_settings}")
        # Получить здоровые инстансы из Consul
        _, services = self.consul.health.service("game-service", passing=True)
        if not services:
            return None

        # Собираем метрики нагрузки
        instance_loads = [
            self.get_instance_load(s["Service"]["ID"], s["Service"]["Address"])
            for s in services
        ]

        # Выбираем инстанс с минимальной загрузкой
        min_load_instance = min(
            instance_loads,
            key=lambda x: x["cpu_usage"] if game_settings.get("resource_level", "low") == "low" else x["ram_usage"]
        )

        # Сохраняем в кэш
        instance_id = min_load_instance["address"]
        await self.cache.set_instance(game_id, instance_id)

        # # Уведомляем через NATS
        # await self.nats_repository.publish_event(
        #     subject_base=f"game.{instance_id}.assign",
        #     payload={
        #         "game_id": game_id,
        #         "user_id": game_settings.get("user_id"),
        #         "instance_id": instance_id
        #     }
        # )
        return instance_id

    async def subscribe_handler(self, event: NatsEvents) -> None:
        def subscribe_wrapper(handler: Callable) -> Any:
            async def callback_wrapper(msg: Msg) -> None:
                try:
                    decoded_data = json.loads(msg.data.decode())
                    response = await handler(data=decoded_data)
                    if msg.reply:
                        await self.nats_repository.publish_simple(
                            subject=msg.reply,
                            payload=response
                        )
                except Exception as e:
                    error_msg = f"Error processing event: {e}"
                    logger.error(error_msg, exc_info=True)
                    if msg and msg.reply:
                        await self.nats_repository.publish_simple(
                            subject=msg.reply,
                            payload={
                                "success": False,
                                "message": error_msg
                            }
                        )

            return callback_wrapper

        match event:
            case NatsEvents.GAME_ID_ASSIGN_GAME_SERVER:
                cb = subscribe_wrapper(handler=self._handler_game_id_assign)
            case _:
                pass

        await self.nats_repository.subscribe(subject=event.value, callback=cb)


    async def _handler_game_id_assign(self, data: dict) -> dict:
        game_id = data["game_id"]
        game_settings = data.get("settings", {"resource_level": "low"})
        instance_id = await self.assign_game_instance(game_id, game_settings)
        logger.info(f"Assigned game {game_id} to instance {instance_id}")
        return {
                "success": True,
                "instance_id": instance_id
            }


    async def initialize_handlers(self) -> None:
        await self.subscribe_handler(event=NatsEvents.GAME_ID_ASSIGN_GAME_SERVER)


    async def run(self):
        logger.info("Game Allocator Service running...")
        await self.nats_repository.get_nc()
        await self.redis_repository.get_redis()
        await self.initialize_handlers()
        await asyncio.Event().wait()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(GameAllocatorService().run())