import asyncio
import json
import logging
from typing import Optional
import nats
import numpy as np
from nats.aio.client import Client as NATS

from ..config import settings

logger = logging.getLogger(__name__)


class NumpyAwareEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyAwareEncoder, self).default(obj)


class NatsRepository:
    def __init__(self) -> None:
        self._nc: NATS | None = None
        logger.info("NatsRepository initialized")

    async def get_nc(self) -> NATS:
        """Подключение к NATS серверу с кешированием"""
        try:
            if self._nc is None or self._nc.is_closed:
                logger.info(f"Connecting to NATS server at {settings.NATS_URL}")
                self._nc = await nats.connect(settings.NATS_URL)
                logger.info(f"Connected to NATS: {settings.NATS_URL}")
            return self._nc
        except Exception as e:
            logger.error(f"Error connecting to NATS at {settings.NATS_URL}: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        try:
            if self._nc:
                logger.info("Disconnecting from NATS server")
                await self._nc.drain()
                self._nc = None
                logger.info("Disconnected from NATS server")
        except Exception as e:
            logger.error(f"Error disconnecting from NATS: {e}", exc_info=True)

    async def _publish_data(self, subject: str, payload: dict) -> bool:
        """
        Internal helper to serialize payload and publish data with retry logic.
        """
        try:
            payload_bytes = json.dumps(payload, cls=NumpyAwareEncoder).encode()
        except TypeError as e:
            logger.error(f"Failed to serialize payload for NATS event {subject}: {e}. Payload: {payload}", exc_info=True)
            return False
        return await self._send_event_with_reconnect(subject=subject, payload_bytes=payload_bytes)

    async def _send_event_with_reconnect(self, subject: str, payload_bytes: bytes, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Send an event to NATS with reconnect logic.
        Returns True if successful, False otherwise.
        """
        attempt: int = 0
        while attempt < max_retries:
            try:
                nc = await self.get_nc()  # Ensures connection is active or tries to reconnect
                if not nc.is_connected:  # Double check after get_nc()
                    logger.warning(f"NATS not connected before publishing to {subject}. Attempting reconnect (try {attempt + 1}/{max_retries}).")
                    # get_nc should handle reconnection, but if it fails silently or nc is closed for other reasons
                    await asyncio.sleep(retry_delay)  # Wait before retrying get_nc
                    attempt += 1
                    continue

                await nc.publish(subject=subject, payload=payload_bytes)
                logger.debug(f"Successfully published to NATS subject: {subject}")
                return True
            except nats.errors.ConnectionClosedError as e:
                logger.warning(f"NATS connection closed while publishing to {subject} (attempt {attempt + 1}/{max_retries}): {e}")
            except nats.errors.TimeoutError as e:
                logger.warning(f"NATS timeout while publishing to {subject} (attempt {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logger.error(f"Unexpected NATS error publishing to {subject}. Attempt {attempt + 1}/{max_retries}. Error: {e}", exc_info=True)

            attempt += 1
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff

        logger.error(f"Failed to publish to NATS subject: {subject} after {max_retries} retries.")
        return False

    async def publish_event(self, subject_base: str, payload: dict, game_id: Optional[str] = None, specific_suffix: Optional[str] = None) -> bool:
        """
        Publishes a JSON payload to a NATS subject.
        Constructs subject like: {subject_base}.{game_id}[.{specific_suffix}]
        Example: game.update.game123 or achievement.unlocked.game123.player456
        """
        subject_parts = [subject_base]
        if game_id:
            subject_parts.append(game_id)
        if specific_suffix:
            subject_parts.append(specific_suffix)
        
        subject = ".".join(subject_parts)
        try:
            success = await self._publish_data(subject=subject, payload=payload)
            if success:
                logger.debug(f"Successfully published event to {subject} with payload: {payload}")
            return success
        except Exception as e:
            logger.error(f"Failed to publish event to {subject} during _publish_data: {e}", exc_info=True)
            return False

    async def publish_simple(self, subject: str, payload: any) -> bool:
        """
        Простая публикация данных в NATS с реконнектом
        """
        payload_bytes = json.dumps(payload, cls=NumpyAwareEncoder).encode()
        return await self._send_event_with_reconnect(subject=subject, payload_bytes=payload_bytes)

    async def subscribe(self, subject: str, callback) -> None:
        """
        Подписка на события NATS
        """
        nc = await self.get_nc()
        await nc.subscribe(subject, cb=callback) 