import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import grpc

from app.config import settings

if TYPE_CHECKING:
    from app.services.event_service import EventService


logger = logging.getLogger(__name__)


try:
    from app.shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger.critical(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )
    raise Exception(e)


class AIInferenceService:
    def __init__(self, event_service: "EventService") -> None:
        self.event_service: "EventService" = event_service
        # self._port: int = settings.AI_SERVICE_GRPC_PORT
        self._action_interval: float = settings.AI_ACTION_INTERVAL
        self._channel: grpc.aio.Channel | None = None
        self._stub: bomberman_ai_pb2_grpc.AIServiceStub | None = None
        self._last_action_at: dict[str, float] = {}
        self._cached_instance: dict[str, Any] | None = None  # Cache for ai-service instance

    async def connect(self) -> None:
        if self._channel is not None:
            return

        # await asyncio.sleep(0.5)

        # Use cached instance if available, otherwise fetch new one
        if not self._cached_instance:
            self._cached_instance = await self.event_service.get_ai_service_instance()
        
        if not self._cached_instance:
            logger.error("ai-service instance is not available to connect to the ai-service-grpc server")
            return
        
        target = f"{self._cached_instance['address']}:{self._cached_instance['grpc_port']}"
        self._channel = grpc.aio.insecure_channel(target=target)
        self._stub = bomberman_ai_pb2_grpc.AIServiceStub(self._channel)
        logger.info(f"Connected to ai-service gRPC at {target}")

    async def disconnect(self) -> None:
        if self._channel is None:
            return
        await self._channel.close()
        self._channel = None
        self._stub = None
        # Note: Keep cached instance for reuse, only clear on explicit reset if needed

    def _can_request_action(self, *, entity_id: str) -> bool:
        now = time.time()
        last_time = self._last_action_at.get(entity_id)
        if last_time is None:
            self._last_action_at[entity_id] = now
            return True
        if now - last_time >= self._action_interval:
            self._last_action_at[entity_id] = now
            return True
        return False

    async def maybe_infer_action(
        self,
        *,
        session_id: str | None,
        entity_id: str,
        grid_values: list[float],
        stats_values: list[float],
    ) -> int | None:
        if not self._can_request_action(entity_id=entity_id):
            return None
        await self.connect()
        if self._stub is None:
            return None
        request = bomberman_ai_pb2.InferActionRequest(
            session_id=session_id or "",
            entity_id=entity_id,
            observation=bomberman_ai_pb2.Observation(
                grid_values=grid_values,
                stats_values=stats_values,
            ),
        )
        try:
            response = await self._stub.InferAction(request)
            return int(response.action)
        except Exception as exc:
            logger.error(f"AI inference failed: {exc}", exc_info=True)
            await self.disconnect()
            return 0