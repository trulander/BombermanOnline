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
        self._action_interval: float = settings.AI_ACTION_INTERVAL
        self._channel: grpc.aio.Channel | None = None
        self._stub: bomberman_ai_pb2_grpc.AIServiceStub | None = None
        self._last_action_at: dict[str, float] = {}
        self._cached_instance: dict[str, Any] | None = None  # Cache for ai-service instance
        # Lock to avoid races between connect and soft reset from concurrent tasks
        self._connection_lock: asyncio.Lock = asyncio.Lock()
        # Consecutive inference errors; used for backoff and reset on success
        self._consecutive_errors: int = 0

    def _reset_channel_state(self) -> None:
        """
        Soft reset: drop channel/stub/cache without calling channel.close().
        Used on inference errors to avoid blocking the event loop (close() can block).
        Full disconnect with close() is only used at shutdown in main.py.
        """
        self._channel = None
        self._stub = None
        self._cached_instance = None

    async def connect(self) -> None:
        async with self._connection_lock:
            if self._channel is not None:
                return

            if not self._cached_instance:
                self._cached_instance = await self.event_service.get_ai_service_instance()

            if not self._cached_instance:
                self._consecutive_errors += 1
                logger.error("ai-service instance is not available to connect to the ai-service-grpc server")
                return

            target = f"{self._cached_instance['address']}:{self._cached_instance['grpc_port']}"
            self._channel = grpc.aio.insecure_channel(target=target)
            self._stub = bomberman_ai_pb2_grpc.AIServiceStub(self._channel)
            logger.info(f"Connected to ai-service gRPC at {target}")

    async def disconnect(self) -> None:
        """Full disconnect with channel.close(); use only at shutdown (e.g. main.py)."""
        async with self._connection_lock:
            if self._channel is None:
                return
            await self._channel.close()
            self._channel = None
            self._stub = None
            # Do not clear _cached_instance on explicit shutdown

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

    def _get_backoff_seconds(self) -> float:
        """Compute backoff delay from consecutive error count (capped at config max)."""
        if self._consecutive_errors <= 0:
            return 0.0
        delay = (
            settings.AI_INFERENCE_BACKOFF_INITIAL_SEC
            + settings.AI_INFERENCE_BACKOFF_STEP_SEC * (self._consecutive_errors - 1)
        )
        return min(delay, settings.AI_INFERENCE_BACKOFF_MAX_SEC)

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

        # After consecutive errors, sleep before next attempt (shared backoff for all entities)
        backoff = self._get_backoff_seconds()
        if backoff > 0:
            await asyncio.sleep(backoff)

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
            response = await asyncio.wait_for(
                self._stub.InferAction(request),
                timeout=settings.AI_INFERENCE_TIMEOUT_SEC,
            )
            self._consecutive_errors = 0
            return int(response.action)
        except asyncio.TimeoutError as exc:
            logger.error(f"AI inference timeout after {settings.AI_INFERENCE_TIMEOUT_SEC}s: {exc}", exc_info=True)
            async with self._connection_lock:
                self._consecutive_errors += 1
                self._reset_channel_state()
            return 0
        except Exception as exc:
            logger.error(f"AI inference failed: {exc}", exc_info=True)
            async with self._connection_lock:
                self._consecutive_errors += 1
                self._reset_channel_state()
            return 0
