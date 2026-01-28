import asyncio
import json
import logging
import threading
import time
from collections.abc import Callable
from typing import TypeVar

import nats
from nats.aio.msg import Msg
from nats.aio.client import Client as NATSClient


logger = logging.getLogger(__name__)

TResult = TypeVar("TResult")


class NatsRepository:
    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc: NATSClient | None = None
        self.thread: threading.Thread | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.owns_loop = False
        self.loop_ready = threading.Event()

    def _run_loop(self) -> None:
        if not self.loop:
            return
        asyncio.set_event_loop(self.loop)
        self.loop_ready.set()
        self.loop.run_forever()

    def _ensure_loop(self) -> None:
        if self.loop and self.thread and self.thread.is_alive():
            return
        if self.loop and self.loop.is_running():
            return
        self.loop_ready.clear()
        self.loop = asyncio.new_event_loop()
        self.owns_loop = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.loop_ready.wait()

    def _set_external_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.thread = None
        self.owns_loop = False

    def _is_connected(self) -> bool:
        if not self.nc:
            return False
        if getattr(self.nc, "is_closed", False):
            return False
        if hasattr(self.nc, "is_connected"):
            return bool(self.nc.is_connected)
        return True

    def _ensure_connected(self) -> None:
        if self._is_connected():
            return
        self.connect()

    async def _aensure_connected(self) -> None:
        if self._is_connected():
            return
        await self.aconnect()

    def _execute_with_reconnect(
        self,
        execute: Callable[[], TResult],
        operation_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> TResult | None:
        attempt = 0
        while attempt < max_retries:
            try:
                self._ensure_connected()
                return execute()
            except nats.errors.ConnectionClosedError as e:
                logger.warning(msg=f"NATS connection closed during {operation_name} (attempt {attempt + 1}/{max_retries}): {e}")
            except nats.errors.TimeoutError as e:
                logger.warning(msg=f"NATS timeout during {operation_name} (attempt {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logger.error(msg=f"Unexpected NATS error during {operation_name}: {e}", exc_info=True)
                return None
            self.nc = None
            attempt += 1
            if attempt < max_retries:
                time.sleep(seconds=retry_delay * (attempt + 1))
        logger.error(msg=f"Failed {operation_name} after {max_retries} retries.")
        return None

    async def _aexecute_with_reconnect(
        self,
        execute: Callable[[], TResult],
        operation_name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> TResult | None:
        attempt = 0
        while attempt < max_retries:
            try:
                await self._aensure_connected()
                result = execute()
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except nats.errors.ConnectionClosedError as e:
                logger.warning(msg=f"NATS connection closed during {operation_name} (attempt {attempt + 1}/{max_retries}): {e}")
            except nats.errors.TimeoutError as e:
                logger.warning(msg=f"NATS timeout during {operation_name} (attempt {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logger.error(msg=f"Unexpected NATS error during {operation_name}: {e}", exc_info=True)
                return None
            self.nc = None
            attempt += 1
            if attempt < max_retries:
                await asyncio.sleep(delay=retry_delay * (attempt + 1))
        logger.error(msg=f"Failed {operation_name} after {max_retries} retries.")
        return None

    def _stop_loop(self) -> None:
        if not self.loop or not self.thread or not self.owns_loop:
            return
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        self.loop.close()
        self.loop = None
        self.thread = None

    def connect(self) -> None:
        try:
            self._ensure_loop()
            future = asyncio.run_coroutine_threadsafe(
                coro=nats.connect(servers=self.nats_url),
                loop=self.loop,
            )
            self.nc = future.result()
            logger.info("Connected to NATS server.")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def aconnect(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            if self.loop is None:
                self._set_external_loop(loop=loop)
            self.nc = await nats.connect(servers=self.nats_url)
            logger.info("Connected to NATS server.")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    def disconnect(self) -> None:
        if self.nc:
            future = asyncio.run_coroutine_threadsafe(
                coro=self.nc.close(),
                loop=self.loop,
            )
            future.result()
            logger.info("Disconnected from NATS server.")
            self.nc = None
        self._stop_loop()

    async def adisconnect(self) -> None:
        if self.nc:
            await self.nc.close()
            logger.info("Disconnected from NATS server.")
            self.nc = None
        if self.owns_loop:
            self._stop_loop()

    def publish(self, subject: str, data: dict[str, object]) -> None:
        try:
            payload = json.dumps(data).encode(encoding="utf-8")
            result = self._execute_with_reconnect(
                execute=lambda: asyncio.run_coroutine_threadsafe(
                    coro=self.nc.publish(subject=subject, payload=payload),
                    loop=self.loop,
                ).result(),
                operation_name=f"publish to {subject}",
            )
            if result is not None:
                logger.debug(f"Published message to {subject}: {data}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}", exc_info=True)

    async def apublish(self, subject: str, data: dict[str, object]) -> None:
        try:
            payload = json.dumps(data).encode(encoding="utf-8")
            result = await self._aexecute_with_reconnect(
                execute=lambda: self.nc.publish(subject=subject, payload=payload),
                operation_name=f"publish to {subject}",
            )
            if result is not None:
                logger.debug(f"Published message to {subject}: {data}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}", exc_info=True)

    def subscribe(self, subject: str, callback: Callable[[dict[str, object]], object]) -> None:
        try:
            async def message_handler(msg) -> None:
                data = json.loads(s=msg.data.decode(encoding="utf-8"))
                result = callback(data)
                if asyncio.iscoroutine(result):
                    await result

            result = self._execute_with_reconnect(
                execute=lambda: asyncio.run_coroutine_threadsafe(
                    coro=self.nc.subscribe(subject=subject, cb=message_handler),
                    loop=self.loop,
                ).result(),
                operation_name=f"subscribe to {subject}",
            )
            if result is not None:
                logger.info(f"Subscribed to NATS subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}", exc_info=True)

    async def asubscribe(self, subject: str, callback: Callable[[dict[str, object]], object]) -> None:
        try:
            async def message_handler(msg) -> None:
                data = json.loads(s=msg.data.decode(encoding="utf-8"))
                result = callback(data)
                if asyncio.iscoroutine(result):
                    await result

            result = await self._aexecute_with_reconnect(
                execute=lambda: self.nc.subscribe(subject=subject, cb=message_handler),
                operation_name=f"subscribe to {subject}",
            )
            if result is not None:
                logger.info(f"Subscribed to NATS subject: {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}", exc_info=True)

    def request(self, subject: str, data: dict[str, object], timeout: float = 5.0) -> dict[str, object] | None:
        try:
            payload = json.dumps(data).encode(encoding="utf-8")
            response = self._execute_with_reconnect(
                execute=lambda: asyncio.run_coroutine_threadsafe(
                    coro=self.nc.request(subject=subject, payload=payload, timeout=timeout),
                    loop=self.loop,
                ).result(),
                operation_name=f"request to {subject}",
            )
            if response is None:
                return None
            decoded_response = json.loads(s=response.data.decode(encoding="utf-8"))
            logger.debug(f"Received response from {subject}: {decoded_response}")
            return decoded_response
        except Exception as e:
            logger.error(f"Failed to make NATS request to {subject}: {e}", exc_info=True)
            return None

    async def arequest(self, subject: str, data: dict[str, object], timeout: float = 5.0) -> dict[str, object] | None:
        try:
            payload = json.dumps(data).encode(encoding="utf-8")
            response: Msg | None = await self._aexecute_with_reconnect(
                execute=lambda: self.nc.request(subject=subject, payload=payload, timeout=timeout),
                operation_name=f"request to {subject}",
            )
            if response is None:
                return None
            decoded_response = json.loads(s=response.data.decode(encoding="utf-8"))
            logger.debug(f"Received response from {subject}: {decoded_response}")
            return decoded_response
        except Exception as e:
            logger.error(f"Failed to make NATS request to {subject}: {e}", exc_info=True)
            return None