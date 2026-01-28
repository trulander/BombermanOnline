import logging
import json
from typing import Any

import redis as redis

logger = logging.getLogger(__name__)


class RedisRepository:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        decode_responses: bool = True
    ):
        self.redis = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=decode_responses)
        logger.info(f"Redis client initialized for {host}:{port}/{db}")

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result = self.redis.set(key, value, ex=ex)
            logger.debug(f"Set Redis key {key}: {value}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}", exc_info=True)
            return False

    def get(self, key: str) -> str | None:
        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"Got Redis key {key}: {value}")
                return value
            logger.debug(f"Redis key {key} not found.")
            return None
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}", exc_info=True)
            return None

    def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
        try:
            value = self.redis.get(key)
            if value:
                decoded_value = json.loads(value)
                logger.debug(f"Got JSON Redis key {key}: {decoded_value}")
                return decoded_value
            logger.debug(f"Redis JSON key {key} not found.")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Redis key {key}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON Redis key {key}: {e}", exc_info=True)
            return None

    def delete(self, key: str) -> int:
        try:
            result = self.redis.delete(key)
            logger.debug(f"Deleted Redis key {key}. Count: {result}")
            return int(result)
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}", exc_info=True)
            return 0

    def exists(self, key: str) -> bool:
        try:
            result = self.redis.exists(key)
            logger.debug(f"Checked existence of Redis key {key}: {bool(result)}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking existence of Redis key {key}: {e}", exc_info=True)
            return False

    def hset(self, name: str, key: str, value: Any) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result = self.redis.hset(name, key, value)
            logger.debug(f"HSet Redis hash {name} key {key}: {value}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error HSetting Redis hash {name} key {key}: {e}", exc_info=True)
            return False

    def hget(self, name: str, key: str) -> str | None:
        try:
            value = self.redis.hget(name, key)
            if value:
                logger.debug(f"HGot Redis hash {name} key {key}: {value}")
                return value
            logger.debug(f"Redis hash {name} key {key} not found.")
            return None
        except Exception as e:
            logger.error(f"Error HGetting Redis hash {name} key {key}: {e}", exc_info=True)
            return None

    def hgetall(self, name: str) -> dict[str, str]:
        try:
            result = self.redis.hgetall(name)
            logger.debug(f"HGot all from Redis hash {name}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error HGetting all from Redis hash {name}: {e}", exc_info=True)
            return {}

    def hdel(self, name: str, key: str) -> int:
        try:
            result = self.redis.hdel(name, key)
            logger.debug(f"HDeleted Redis hash {name} key {key}. Count: {result}")
            return int(result)
        except Exception as e:
            logger.error(f"Error HDeleting Redis hash {name} key {key}: {e}", exc_info=True)
            return 0

    def close(self) -> None:
        try:
            self.redis.close()
            logger.info("Redis connection closed.")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}", exc_info=True) 