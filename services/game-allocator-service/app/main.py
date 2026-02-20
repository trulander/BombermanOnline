import logging
import socket
from typing import Callable, Any, Optional

import asyncio
import json
import consul
from prometheus_api_client import PrometheusConnect

from aiohttp import web

from config import settings
from logging_config import configure_logging
from nats_repository import NatsRepository
from game_cache import GameInstanceCache
from redis_repository import RedisRepository
from load_balancer import LoadBalancer
from nats.aio.msg import Msg


logger = logging.getLogger(__name__)


async def health_check_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "healthy",
        "service": settings.SERVICE_NAME
    })


def create_healthcheck_server() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_check_handler)
    return app


async def start_healthcheck_server(port: int) -> None:
    app = create_healthcheck_server()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Healthcheck server started on 0.0.0.0:{port}")


# NatsEvents enum removed - events are now configured via SERVICE_CONFIGS


class GameAllocatorService:
    def __init__(self):
        self.nats_repository = NatsRepository()
        self.redis_repository = RedisRepository()
        self.consul = consul.Consul(host=settings.CONSUL_HOST, port=8500)
        self.prom = PrometheusConnect(url=settings.PROMETHEUS_URL, disable_ssl=True)
        self.cache = GameInstanceCache(redis_repository=self.redis_repository, ttl=settings.GAME_CACHE_TTL)
        self.load_balancer = LoadBalancer(
            consul_client=self.consul,
            prometheus_client=self.prom,
            load_threshold=settings.LOAD_THRESHOLD
        )

    async def get_service_instance(
        self,
        service_name: str,
        resource_type: str = "cpu"
    ) -> Optional[dict]:
        """
        Get best service instance using load balancing logic.
        
        Args:
            service_name: Name of the service
            resource_type: Type of resource to optimize for ("cpu" or "ram")
            
        Returns:
            Instance dictionary with address, rest_port, grpc_port or None
        """
        logger.debug(f"get_service_instance - service_name:{service_name}, resource_type:{resource_type}")
        
        # Get healthy instances from Consul
        _, services = self.consul.health.service(service_name, passing=True)
        if not services:
            logger.warning(f"No healthy {service_name} instances found")
            return None
        
        # Use LoadBalancer to select best instance
        instance = await self.load_balancer.select_best_instance(
            service_name=service_name,
            instances=services,
            resource_type=resource_type
        )
        
        if instance:
            logger.debug(f"get_service_instance - selected instance: {instance}")
        else:
            logger.warning(f"get_service_instance - no instance selected for {service_name}")
        
        return instance

    async def get_all_service_instances(self, service_name: str) -> list[dict]:
        """
        Get all healthy service instances from Consul.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of instance dictionaries with address, rest_port, grpc_port
        """
        logger.debug(f"get_all_service_instances - service_name:{service_name}")
        
        _, services = self.consul.health.service(service_name, passing=True)
        if not services:
            logger.warning(f"No healthy {service_name} instances found")
            return []
        
        instances = [
            {
                "address": s["Service"]["Address"],
                "rest_port": int(s["Service"].get("Meta", {}).get("rest_api_port", 0)),
                "grpc_port": int(s["Service"].get("Meta", {}).get("grpc_port", 0)),
            }
            for s in services
        ]
        
        logger.debug(f"get_all_service_instances - found {len(instances)} instances")
        return instances

    async def subscribe_handler(self, subject: str, handler: Callable) -> None:
        """
        Subscribe to NATS event with handler.
        
        Args:
            subject: NATS subject to subscribe to
            handler: Handler function to process messages
        """
        def subscribe_wrapper(handler_func: Callable) -> Any:
            async def callback_wrapper(msg: Msg) -> None:
                try:
                    decoded_data = json.loads(msg.data.decode())
                    response = await handler_func(data=decoded_data)
                    if msg.reply:
                        await self.nats_repository.publish_simple(
                            subject=msg.reply,
                            payload=response
                        )
                except Exception as e:
                    error_msg = f"Error processing event {subject}: {e}"
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

        cb = subscribe_wrapper(handler)
        await self.nats_repository.subscribe(subject=subject, callback=cb)
        logger.info(f"Subscribed to NATS subject: {subject}")

    def _create_instance_request_handler(self, service_name: str):
        """Create handler for instance request event (returns one instance)."""
        async def handler(data: dict) -> dict:
            logger.debug(f"_handler_instance_request - service_name:{service_name}")
            resource_type = data.get("resource_type", "cpu")
            instance = await self.get_service_instance(
                service_name=service_name,
                resource_type=resource_type
            )
            if instance:
                return {"success": True, "instance": instance}
            else:
                return {"success": False, "message": f"No healthy {service_name} instances available"}
        return handler

    def _create_instances_request_handler(self, service_name: str):
        """Create handler for instances request event (returns all instances)."""
        async def handler(data: dict) -> dict:
            logger.debug(f"_handler_instances_request - service_name:{service_name}")
            instances = await self.get_all_service_instances(service_name=service_name)
            return {"success": True, "instances": instances}
        return handler

    def _create_assign_request_handler(self, service_name: str):
        """Create handler for assign request event (for game-service)."""
        async def handler(data: dict) -> dict:
            logger.debug(f"_handler_assign_request - service_name:{service_name}")
            game_id = data.get("game_id")
            if not game_id:
                return {"success": False, "message": "game_id is required"}
            
            game_settings = data.get("settings", {"resource_level": "low"})
            resource_type = "cpu" if game_settings.get("resource_level", "low") == "low" else "ram"
            
            instance = await self.get_service_instance(
                service_name=service_name,
                resource_type=resource_type
            )
            
            if not instance:
                return {"success": False, "message": f"No healthy {service_name} instances available"}
            
            instance_id = instance["address"]
            await self.cache.set_instance(game_id, instance_id)
            logger.info(f"Assigned game {game_id} to {service_name} instance {instance_id}")
            
            return {
                "success": True,
                "instance_id": instance_id
            }
        return handler


    async def initialize_handlers(self) -> None:
        """
        Initialize NATS handlers based on SERVICE_CONFIGS.
        Automatically registers handlers for all configured services.
        """
        logger.info("Initializing NATS handlers from SERVICE_CONFIGS")
        
        for service_config in settings.SERVICE_CONFIGS:
            service_name = service_config["service_name"]
            
            # Register instance request handler (one instance)
            if "instance_request_event" in service_config:
                event = service_config["instance_request_event"]
                handler = self._create_instance_request_handler(service_name)
                await self.subscribe_handler(subject=event, handler=handler)
            
            # Register instances request handler (all instances)
            if "instances_request_event" in service_config:
                event = service_config["instances_request_event"]
                handler = self._create_instances_request_handler(service_name)
                await self.subscribe_handler(subject=event, handler=handler)
            
            # Register assign request handler (for game-service)
            if "assign_event" in service_config:
                event = service_config["assign_event"]
                handler = self._create_assign_request_handler(service_name)
                await self.subscribe_handler(subject=event, handler=handler)
        
        logger.info("All NATS handlers initialized")


    async def run(self):
        logger.info("Game Allocator Service running...")
        await self.nats_repository.get_nc()
        await self.redis_repository.get_redis()
        await self.initialize_handlers()
        asyncio.create_task(start_healthcheck_server(port=settings.PORT))
        await asyncio.Event().wait()


def register_service():
    logger.info(f"registering in the consul service")
    service_name = settings.SERVICE_NAME
    c = consul.Consul(host=settings.CONSUL_HOST, port=8500)
    service_id = f"{service_name}-{socket.gethostname()}"
    c.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=socket.gethostname(),
        port=settings.PORT,
        tags=["traefik"],
        check=consul.Check.http(
            url=f"http://{socket.gethostname()}:{settings.PORT}/health",
            interval="10s",
            timeout="1s",
            deregister="60s"
        )
    )


if __name__ == "__main__":
    configure_logging()
    register_service()
    asyncio.run(GameAllocatorService().run())