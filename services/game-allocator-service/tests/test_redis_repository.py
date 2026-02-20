"""
Tests for RedisRepository class.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from redis_repository import RedisRepository


class TestRedisRepositoryInit:
    """Tests for RedisRepository.__init__."""
    
    def test_init_with_redis_none(self):
        """Test initialization with _redis = None."""
        repo = RedisRepository()
        assert repo._redis is None


class TestRedisRepositoryGetRedis:
    """Tests for RedisRepository.get_redis."""
    
    @pytest.mark.asyncio
    async def test_get_redis_first_connection(self, fake_redis_server):
        """Test first connection to Redis."""
        repo = RedisRepository()
        # Mock ping to be async
        fake_redis_server.ping = AsyncMock(return_value=True)
        with patch('redis_repository.redis.Redis', return_value=fake_redis_server):
            result = await repo.get_redis()
            assert result == fake_redis_server
            assert repo._redis == fake_redis_server
    
    @pytest.mark.asyncio
    async def test_get_redis_existing_connection(self, fake_redis_server):
        """Test returning existing connection."""
        repo = RedisRepository()
        repo._redis = fake_redis_server
        
        result = await repo.get_redis()
        assert result == fake_redis_server
    
    @pytest.mark.asyncio
    async def test_get_redis_connection_test(self, fake_redis_server):
        """Test connection test via ping()."""
        repo = RedisRepository()
        fake_redis_server.ping = AsyncMock(return_value=True)
        
        with patch('redis_repository.redis.Redis', return_value=fake_redis_server):
            await repo.get_redis()
            fake_redis_server.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_redis_connection_error(self):
        """Test handling of connection errors."""
        repo = RedisRepository()
        
        with patch('redis_repository.redis.Redis', side_effect=Exception("Connection error")):
            with pytest.raises(Exception):
                await repo.get_redis()


class TestRedisRepositoryDisconnect:
    """Tests for RedisRepository.disconnect."""
    
    @pytest.mark.asyncio
    async def test_disconnect_active_connection(self, fake_redis_server):
        """Test closing active connection."""
        repo = RedisRepository()
        # Create a mock that can be awaited
        mock_redis = MagicMock()
        mock_redis.close = AsyncMock()
        repo._redis = mock_redis
        
        await repo.disconnect()
        
        mock_redis.close.assert_called_once()
        assert repo._redis is None
    
    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self):
        """Test handling when no connection exists."""
        repo = RedisRepository()
        repo._redis = None
        
        # Should not raise exception
        await repo.disconnect()
    
    @pytest.mark.asyncio
    async def test_disconnect_error_handling(self, fake_redis_server):
        """Test error handling during disconnect."""
        repo = RedisRepository()
        # Create a mock that raises exception when awaited
        mock_redis = MagicMock()
        mock_redis.close = AsyncMock(side_effect=Exception("Close error"))
        repo._redis = mock_redis
        
        # Should handle error gracefully
        await repo.disconnect()


class TestRedisRepositorySet:
    """Tests for RedisRepository.set."""
    
    @pytest.mark.asyncio
    async def test_set_success_no_ttl(self):
        """Test successful save without TTL."""
        repo = RedisRepository()
        # Use fully mocked async Redis client
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.set(key="test_key", value="test_value", expire=0)
        
        assert result is True
        mock_redis.set.assert_called_once()
        # Check that value was JSON serialized
        call_args = mock_redis.set.call_args
        # When expire=0, ex should be None
        assert call_args[1].get("ex") is None or "ex" not in call_args[1]
    
    @pytest.mark.asyncio
    async def test_set_success_with_ttl(self):
        """Test successful save with TTL."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.set(key="test_key", value="test_value", expire=60)
        
        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 60
    
    @pytest.mark.asyncio
    async def test_set_json_serialization(self):
        """Test JSON serialization of value."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        test_value = {"key": "value", "number": 42}
        await repo.set(key="test_key", value=test_value, expire=0)
        
        call_args = mock_redis.set.call_args
        serialized_value = call_args[0][1]
        assert json.loads(serialized_value) == test_value
    
    @pytest.mark.asyncio
    async def test_set_error_handling(self):
        """Test error handling."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.set(key="test_key", value="test_value", expire=0)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_set_returns_false(self):
        """Test when set returns False (Redis operation failed)."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.set = AsyncMock(return_value=False)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.set(key="test_key", value="test_value", expire=0)
        
        assert result is False


class TestRedisRepositoryGet:
    """Tests for RedisRepository.get."""
    
    @pytest.mark.asyncio
    async def test_get_existing_key(self):
        """Test successful retrieval of existing key."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"key": "value", "number": 42}))
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        test_value = {"key": "value", "number": 42}
        result = await repo.get(key="test_key")
        
        assert result == test_value
    
    @pytest.mark.asyncio
    async def test_get_json_deserialization(self):
        """Test JSON deserialization."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        test_value = {"key": "value"}
        mock_redis.get = AsyncMock(return_value=json.dumps(test_value))
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.get(key="test_key")
        
        assert isinstance(result, dict)
        assert result == test_value
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test return None for nonexistent key."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.get(key="nonexistent_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_json_decode_error(self):
        """Test handling of JSON decode errors."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="invalid json")
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.get(key="test_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_connection_error(self):
        """Test handling of connection errors."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Connection error"))
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.get(key="test_key")
        
        assert result is None


class TestRedisRepositoryDelete:
    """Tests for RedisRepository.delete."""
    
    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        """Test successful deletion of existing key."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.delete(key="test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self):
        """Test return False for nonexistent key."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(return_value=0)
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.delete(key="nonexistent_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_error_handling(self):
        """Test error handling."""
        repo = RedisRepository()
        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        mock_redis.connection_pool = MagicMock()
        mock_redis.connection_pool.connection_class = MagicMock()
        repo._redis = mock_redis
        
        result = await repo.delete(key="test_key")
        
        assert result is False

