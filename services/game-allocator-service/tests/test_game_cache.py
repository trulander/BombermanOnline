"""
Tests for GameInstanceCache class.
"""
import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from game_cache import GameInstanceCache


class TestGameInstanceCacheInit:
    """Tests for GameInstanceCache.__init__."""
    
    def test_init_with_ttl(self):
        """Test initialization with correct TTL."""
        # Use a simple mock instead of fixture to avoid async issues
        mock_redis_repo = MagicMock()
        cache = GameInstanceCache(redis_repository=mock_redis_repo, ttl=60)
        assert cache.ttl == 60
        assert cache.redis_repository == mock_redis_repo
    
    def test_init_empty_local_cache(self):
        """Test initialization of empty local_cache."""
        # Use a simple mock instead of fixture to avoid async issues
        mock_redis_repo = MagicMock()
        cache = GameInstanceCache(redis_repository=mock_redis_repo, ttl=60)
        assert isinstance(cache.local_cache, dict)
        assert cache.local_cache == {}


class TestGameInstanceCacheGetInstance:
    """Tests for GameInstanceCache.get_instance."""
    
    @pytest.mark.asyncio
    async def test_get_instance_from_local_cache_valid(self, redis_repository):
        """Test retrieval from local cache when TTL not expired."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        # Set in local cache
        cache.local_cache[game_id] = {
            "instance_id": instance_id,
            "timestamp": time.time()
        }
        
        result = await cache.get_instance(game_id)
        
        assert result == instance_id
    
    @pytest.mark.asyncio
    async def test_get_instance_local_cache_expired(self, redis_repository):
        """Test skipping local cache when TTL expired."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        # Set in local cache with expired timestamp
        cache.local_cache[game_id] = {
            "instance_id": instance_id,
            "timestamp": time.time() - 100  # Expired
        }
        
        # Mock Redis to return None
        redis_repository.get = AsyncMock(return_value=None)
        
        result = await cache.get_instance(game_id)
        
        assert result is None
        redis_repository.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_instance_from_redis(self, redis_repository):
        """Test retrieval from Redis when not in local cache."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.get = AsyncMock(return_value=instance_id)
        redis_repository.set = AsyncMock(return_value=True)
        
        result = await cache.get_instance(game_id)
        
        assert result == instance_id
        redis_repository.get.assert_called_once_with(key=f"games:{game_id}")
        # Should update local cache
        assert game_id in cache.local_cache
        assert cache.local_cache[game_id]["instance_id"] == instance_id
    
    @pytest.mark.asyncio
    async def test_get_instance_update_local_cache_from_redis(self, redis_repository):
        """Test updating local cache from Redis."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.get = AsyncMock(return_value=instance_id)
        redis_repository.set = AsyncMock(return_value=True)
        
        await cache.get_instance(game_id)
        
        assert game_id in cache.local_cache
        assert cache.local_cache[game_id]["instance_id"] == instance_id
        assert "timestamp" in cache.local_cache[game_id]
    
    @pytest.mark.asyncio
    async def test_get_instance_not_found_anywhere(self, redis_repository):
        """Test return None when not found anywhere."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        
        redis_repository.get = AsyncMock(return_value=None)
        
        result = await cache.get_instance(game_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_instance_extend_ttl_in_redis(self, redis_repository):
        """Test extending TTL in Redis when retrieving."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.get = AsyncMock(return_value=instance_id)
        redis_repository.set = AsyncMock(return_value=True)
        
        await cache.get_instance(game_id)
        
        # Should call set with extended TTL (ttl + 10)
        redis_repository.set.assert_called_once_with(
            key=f"games:{game_id}",
            expire=70,  # 60 + 10
            value=instance_id
        )


class TestGameInstanceCacheSetInstance:
    """Tests for GameInstanceCache.set_instance."""
    
    @pytest.mark.asyncio
    async def test_set_instance_save_to_redis_with_ttl(self):
        """Test saving to Redis with TTL."""
        # Create a fresh mock repository to avoid issues with fixture
        mock_redis_repo = MagicMock()
        mock_redis_repo.set = AsyncMock(return_value=True)
        cache = GameInstanceCache(redis_repository=mock_redis_repo, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        await cache.set_instance(game_id, instance_id)
        
        mock_redis_repo.set.assert_called_once_with(
            key=f"games:{game_id}",
            expire=70,  # ttl + 10
            value=instance_id
        )
    
    @pytest.mark.asyncio
    async def test_set_instance_update_local_cache(self, redis_repository):
        """Test updating local cache."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.set = AsyncMock(return_value=True)
        
        await cache.set_instance(game_id, instance_id)
        
        assert game_id in cache.local_cache
        assert cache.local_cache[game_id]["instance_id"] == instance_id
        assert "timestamp" in cache.local_cache[game_id]
    
    @pytest.mark.asyncio
    async def test_set_instance_correct_ttl(self, redis_repository):
        """Test correct TTL calculation (ttl + 10)."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=100)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.set = AsyncMock(return_value=True)
        
        await cache.set_instance(game_id, instance_id)
        
        call_args = redis_repository.set.call_args
        assert call_args[1]["expire"] == 110  # 100 + 10
    
    @pytest.mark.asyncio
    async def test_set_instance_save_timestamp(self, redis_repository):
        """Test saving timestamp in local cache."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        game_id = "test_game_1"
        instance_id = "192.168.1.10"
        
        redis_repository.set = AsyncMock(return_value=True)
        
        before_time = time.time()
        await cache.set_instance(game_id, instance_id)
        after_time = time.time()
        
        timestamp = cache.local_cache[game_id]["timestamp"]
        assert before_time <= timestamp <= after_time

