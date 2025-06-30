import asyncio
import json
import logging
from typing import Any, Callable

import nats
from nats.aio.client import Client as NATSClient


logger = logging.getLogger(__name__)


class NatsRepository:
    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc: NATSClient | None = None

    async def connect(self) -> None:
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info("Connected to NATS server.")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self) -> None:
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS server.")

    async def publish(self, subject: str, data: dict[str, Any]) -> None:
        if not self.nc:
            logger.warning("NATS not connected. Cannot publish message.")
            return
        try:
            payload = json.dumps(data).encode('utf-8')
            await self.nc.publish(subject, payload)
            logger.debug(f"Published message to {subject}: {data}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}", exc_info=True)

    async def subscribe(self, subject: str, callback: Callable[[dict[str, Any]], Any]) -> None:
        if not self.nc:
            logger.warning("NATS not connected. Cannot subscribe to subject.")
            return
        try:
            async def message_handler(msg):
                data = json.loads(msg.data.decode('utf-8'))
                await callback(data) # Ensure callback is awaited if it's an async function

            await self.nc.subscribe(subject, cb=message_handler)
            logger.info(f"Subscribed to NATS subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}", exc_info=True)

    async def request(self, subject: str, data: dict[str, Any], timeout: float = 5.0) -> dict[str, Any] | None:
        if not self.nc:
            logger.warning("NATS not connected. Cannot make request.")
            return None
        try:
            payload = json.dumps(data).encode('utf-8')
            response = await self.nc.request(subject, payload, timeout=timeout)
            decoded_response = json.loads(response.data.decode('utf-8'))
            logger.debug(f"Received response from {subject}: {decoded_response}")
            return decoded_response
        except nats.errors.TimeoutError:
            logger.error(f"NATS request to {subject} timed out after {timeout} seconds.")
            return None
        except Exception as e:
            logger.error(f"Failed to make NATS request to {subject}: {e}", exc_info=True)
            return None 