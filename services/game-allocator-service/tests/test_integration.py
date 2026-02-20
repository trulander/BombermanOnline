"""
Integration tests for game-allocator-service components.
"""
import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from main import GameAllocatorService
from load_balancer import LoadBalancer
from nats_repository import NatsRepository
from redis_repository import RedisRepository
from game_cache import GameInstanceCache


class TestGameAllocatorServiceIntegration:
    """Integration tests for GameAllocatorService with other components."""
    
    @pytest.mark.asyncio
    async def test_service_with_load_balancer_and_consul_prometheus(self, mocker, sample_consul_services):
        """Test GameAllocatorService + LoadBalancer + Consul + Prometheus integration."""
        service = GameAllocatorService()
        
        # Mock Consul
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        
        # Mock Prometheus responses
        service.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU for instance 1
            [{"value": [None, "1024"]}],  # RAM for instance 1
            [{"value": [None, "11.0"]}],  # CPU for instance 2
            [{"value": [None, "2048"]}],  # RAM for instance 2
            [{"value": [None, "12.0"]}],  # CPU for instance 3
            [{"value": [None, "3072"]}],  # RAM for instance 3
        ])
        
        result = await service.get_service_instance("game-service", "cpu")
        
        assert result is not None
        assert "address" in result
        assert "rest_port" in result
        assert "grpc_port" in result
    
    @pytest.mark.asyncio
    async def test_service_nats_repository_full_cycle(self, mocker):
        """Test GameAllocatorService + NatsRepository full request-response cycle."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        service.nats_repository.publish_simple = AsyncMock()
        
        # Create handler
        handler = service._create_instance_request_handler("game-service")
        
        # Mock Consul and LoadBalancer
        service.consul.health.service = MagicMock(return_value=(None, [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10",
                "Meta": {"rest_api_port": "5002", "grpc_port": "50051"}
            }
        }]))
        service.load_balancer.select_best_instance = AsyncMock(return_value={
            "address": "192.168.1.10",
            "rest_port": 5002,
            "grpc_port": 50051
        })
        
        # Simulate NATS message processing
        mock_msg = MagicMock()
        mock_msg.data = b'{"resource_type": "cpu"}'
        mock_msg.reply = "reply.subject"
        
        await service.subscribe_handler("test.subject", handler)
        call_args = service.nats_repository.subscribe.call_args
        # subscribe(subject=subject, callback=cb) - callback is in kwargs
        callback = call_args.kwargs.get("callback") or (call_args.args[1] if len(call_args.args) > 1 else None)
        
        await callback(mock_msg)
        
        # Should publish response
        service.nats_repository.publish_simple.assert_called_once()
        pub_call_args = service.nats_repository.publish_simple.call_args
        subject = pub_call_args.args[0] if pub_call_args.args else pub_call_args.kwargs.get("subject")
        payload = pub_call_args.args[1] if len(pub_call_args.args) > 1 else pub_call_args.kwargs.get("payload")
        assert subject == "reply.subject"
        assert payload["success"] is True
    
    @pytest.mark.asyncio
    async def test_service_redis_repository_game_cache(self, fake_redis_server):
        """Test GameAllocatorService + RedisRepository + GameInstanceCache integration."""
        redis_repo = RedisRepository()
        # Mock async methods for fakeredis
        fake_redis_server.set = AsyncMock(return_value=True)
        fake_redis_server.get = AsyncMock(return_value='"192.168.1.10"')
        redis_repo._redis = fake_redis_server
        
        cache = GameInstanceCache(redis_repository=redis_repo, ttl=60)
        
        # Set instance
        await cache.set_instance("game123", "192.168.1.10")
        
        # Get instance
        result = await cache.get_instance("game123")
        
        assert result == "192.168.1.10"
    
    @pytest.mark.asyncio
    async def test_nats_events_end_to_end(self, mocker):
        """Test NATS events end-to-end processing."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        service.nats_repository.publish_simple = AsyncMock()
        
        # Mock dependencies
        service.consul.health.service = MagicMock(return_value=(None, [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10",
                "Meta": {"rest_api_port": "5002", "grpc_port": "50051"}
            }
        }]))
        service.load_balancer.select_best_instance = AsyncMock(return_value={
            "address": "192.168.1.10",
            "rest_port": 5002,
            "grpc_port": 50051
        })
        service.cache.set_instance = AsyncMock()
        
        # Initialize handlers
        await service.initialize_handlers()
        
        # Verify handlers were registered - subscribe_handler is a method, not a mock
        # Check that nats_repository.subscribe was called
        assert service.nats_repository.subscribe.call_count > 0


class TestLoadBalancerRoundRobinPerformance:
    """Performance tests for round-robin rotation."""
    
    @pytest.mark.asyncio
    async def test_round_robin_under_load(self, load_balancer):
        """Test round-robin rotation under load (multiple parallel requests)."""
        instances = [
            {"address": "addr1", "cpu_usage": 10.0, "ram_usage": 1000.0},
            {"address": "addr2", "cpu_usage": 11.0, "ram_usage": 2000.0},
            {"address": "addr3", "cpu_usage": 12.0, "ram_usage": 3000.0},
        ]
        
        # Make 100 parallel requests
        tasks = [
            load_balancer.select_instance_with_rotation(
                service_name="game-service",
                equal_load_instances=instances,
                resource_type="cpu"
            )
            for _ in range(100)
        ]
        
        results = await asyncio.gather(*tasks)
        addresses = [r["address"] for r in results]
        
        # All results should be valid
        assert all(addr in ["addr1", "addr2", "addr3"] for addr in addresses)
        
        # Distribution should be relatively even
        addr1_count = addresses.count("addr1")
        addr2_count = addresses.count("addr2")
        addr3_count = addresses.count("addr3")
        
        # Each should appear roughly 33 times (with some variance)
        assert 25 <= addr1_count <= 40
        assert 25 <= addr2_count <= 40
        assert 25 <= addr3_count <= 40


class TestLoadBalancerPerformance:
    """Performance tests for LoadBalancer."""
    
    def test_get_instance_load_with_many_instances(self, load_balancer, mocker):
        """Test performance of get_instance_load with many instances."""
        load_balancer.prom.custom_query = MagicMock(return_value=[{"value": [None, "10.0"]}])
        
        # Simulate querying 100 instances
        for i in range(100):
            load_balancer.get_instance_load(
                service_name="game-service",
                instance_id=f"instance-{i}",
                address=f"192.168.1.{i}"
            )
        
        # Should have called Prometheus 200 times (CPU + RAM for each)
        assert load_balancer.prom.custom_query.call_count == 200


class TestCachePerformance:
    """Performance tests for caching."""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, redis_repository):
        """Test cache performance."""
        cache = GameInstanceCache(redis_repository=redis_repository, ttl=60)
        
        # Set many instances
        for i in range(100):
            await cache.set_instance(f"game{i}", f"192.168.1.{i}")
        
        # Get many instances (should use local cache)
        import time
        start_time = time.time()
        
        for i in range(100):
            await cache.get_instance(f"game{i}")
        
        elapsed = time.time() - start_time
        
        # Should be fast (local cache lookup)
        assert elapsed < 1.0  # Should complete in less than 1 second

