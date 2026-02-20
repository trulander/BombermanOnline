"""
Tests for GameAllocatorService class.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nats.aio.msg import Msg

from main import (
    GameAllocatorService,
    health_check_handler,
    create_healthcheck_server,
    start_healthcheck_server,
    register_service
)
from config import settings


class TestGameAllocatorServiceInit:
    """Tests for GameAllocatorService.__init__."""
    
    def test_init_all_dependencies(self, mocker):
        """Test initialization of all dependencies."""
        mocker.patch('main.consul.Consul')
        mocker.patch('main.PrometheusConnect')
        mocker.patch('main.NatsRepository')
        mocker.patch('main.RedisRepository')
        mocker.patch('main.GameInstanceCache')
        mocker.patch('main.LoadBalancer')
        
        service = GameAllocatorService()
        
        assert service.nats_repository is not None
        assert service.redis_repository is not None
        assert service.consul is not None
        assert service.prom is not None
        assert service.cache is not None
        assert service.load_balancer is not None
    
    def test_init_load_balancer_params(self, mocker):
        """Test LoadBalancer creation with correct parameters."""
        mocker.patch('app.main.consul.Consul')
        mocker.patch('app.main.PrometheusConnect')
        mocker.patch('app.main.NatsRepository')
        mocker.patch('app.main.RedisRepository')
        mocker.patch('app.main.GameInstanceCache')
        
        load_balancer_mock = mocker.patch('main.LoadBalancer')
        
        service = GameAllocatorService()
        
        load_balancer_mock.assert_called_once()
        call_args = load_balancer_mock.call_args
        assert call_args[1]["load_threshold"] == settings.LOAD_THRESHOLD
    
    def test_init_cache_ttl(self, mocker):
        """Test cache initialization with correct TTL."""
        mocker.patch('app.main.consul.Consul')
        mocker.patch('app.main.PrometheusConnect')
        mocker.patch('app.main.NatsRepository')
        mocker.patch('app.main.RedisRepository')
        mocker.patch('app.main.LoadBalancer')
        
        cache_mock = mocker.patch('main.GameInstanceCache')
        
        service = GameAllocatorService()
        
        cache_mock.assert_called_once()
        call_args = cache_mock.call_args
        assert call_args[1]["ttl"] == settings.GAME_CACHE_TTL


class TestGameAllocatorServiceGetServiceInstance:
    """Tests for GameAllocatorService.get_service_instance."""
    
    @pytest.mark.asyncio
    async def test_get_service_instance_success(self, mocker, sample_consul_services):
        """Test successful instance retrieval through LoadBalancer."""
        service = GameAllocatorService()
        
        # Mock Consul
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        
        # Mock LoadBalancer
        mock_instance = {"address": "192.168.1.10", "rest_port": 5002, "grpc_port": 50051}
        service.load_balancer.select_best_instance = AsyncMock(return_value=mock_instance)
        
        result = await service.get_service_instance("game-service", "cpu")
        
        assert result == mock_instance
        service.load_balancer.select_best_instance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_instance_no_healthy_instances(self, mocker):
        """Test when no healthy instances in Consul (returns None)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, []))
        
        result = await service.get_service_instance("game-service", "cpu")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_service_instance_resource_type_passed(self, mocker, sample_consul_services):
        """Test that resource_type is passed correctly to LoadBalancer."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        await service.get_service_instance("game-service", "ram")
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "ram"


class TestGameAllocatorServiceGetAllServiceInstances:
    """Tests for GameAllocatorService.get_all_service_instances."""
    
    @pytest.mark.asyncio
    async def test_get_all_service_instances_success(self, mocker, sample_consul_services):
        """Test successful retrieval of all instances."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        
        result = await service.get_all_service_instances("game-service")
        
        assert len(result) == 3
        assert all("address" in inst for inst in result)
        assert all("rest_port" in inst for inst in result)
        assert all("grpc_port" in inst for inst in result)
    
    @pytest.mark.asyncio
    async def test_get_all_service_instances_no_instances(self, mocker):
        """Test when no healthy instances (returns [])."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, []))
        
        result = await service.get_all_service_instances("game-service")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_all_service_instances_extract_ports(self, mocker, sample_consul_services):
        """Test correct extraction of address, rest_port, grpc_port."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        
        result = await service.get_all_service_instances("game-service")
        
        assert result[0]["address"] == "192.168.1.10"
        assert result[0]["rest_port"] == 5002
        assert result[0]["grpc_port"] == 50051
    
    @pytest.mark.asyncio
    async def test_get_all_service_instances_no_meta(self, mocker):
        """Test handling of missing Meta."""
        services_no_meta = [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10"
            }
        }]
        
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, services_no_meta))
        
        result = await service.get_all_service_instances("game-service")
        
        assert result[0]["rest_port"] == 0
        assert result[0]["grpc_port"] == 0
    
    @pytest.mark.asyncio
    async def test_get_all_service_instances_no_ports_in_meta(self, mocker):
        """Test handling of missing ports in Meta."""
        services_no_ports = [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10",
                "Meta": {}
            }
        }]
        
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, services_no_ports))
        
        result = await service.get_all_service_instances("game-service")
        
        assert result[0]["rest_port"] == 0
        assert result[0]["grpc_port"] == 0


class TestGameAllocatorServiceSubscribeHandler:
    """Tests for GameAllocatorService.subscribe_handler."""
    
    @pytest.mark.asyncio
    async def test_subscribe_handler_success(self, mocker):
        """Test successful subscription to NATS subject."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        
        async def test_handler(data: dict) -> dict:
            return {"success": True}
        
        await service.subscribe_handler("test.subject", test_handler)
        
        service.nats_repository.subscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_handler_successful_response(self, mocker):
        """Test handling successful response (publish to reply)."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        service.nats_repository.publish_simple = AsyncMock()
        
        async def test_handler(data: dict) -> dict:
            return {"success": True, "data": "test"}
        
        # Create mock message with reply
        mock_msg = MagicMock(spec=Msg)
        mock_msg.data = b'{"test": "data"}'
        mock_msg.reply = "reply.subject"
        
        # Get the callback wrapper
        await service.subscribe_handler("test.subject", test_handler)
        call_args = service.nats_repository.subscribe.call_args
        # subscribe(subject=subject, callback=cb) - callback is in kwargs
        callback = call_args.kwargs.get("callback") or (call_args.args[1] if len(call_args.args) > 1 else None)
        
        assert callback is not None, f"Callback should not be None. call_args: {call_args}"
        await callback(mock_msg)
        
        service.nats_repository.publish_simple.assert_called_once()
        pub_call_args = service.nats_repository.publish_simple.call_args
        subject = pub_call_args.args[0] if pub_call_args.args else pub_call_args.kwargs.get("subject")
        assert subject == "reply.subject"
    
    @pytest.mark.asyncio
    async def test_subscribe_handler_exception_in_handler(self, mocker):
        """Test handling exceptions in handler (publish error response)."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        service.nats_repository.publish_simple = AsyncMock()
        
        async def test_handler(data: dict) -> dict:
            raise Exception("Handler error")
        
        mock_msg = MagicMock(spec=Msg)
        mock_msg.data = b'{"test": "data"}'
        mock_msg.reply = "reply.subject"
        
        await service.subscribe_handler("test.subject", test_handler)
        call_args = service.nats_repository.subscribe.call_args
        # subscribe(subject=subject, callback=cb) - callback is in kwargs
        callback = call_args.kwargs.get("callback") or (call_args.args[1] if len(call_args.args) > 1 else None)
        
        assert callback is not None, "Callback should not be None"
        await callback(mock_msg)
        
        service.nats_repository.publish_simple.assert_called_once()
        pub_call_args = service.nats_repository.publish_simple.call_args
        payload = pub_call_args.args[1] if len(pub_call_args.args) > 1 else pub_call_args.kwargs.get("payload")
        assert payload["success"] is False
        assert "error" in payload["message"].lower()
    
    @pytest.mark.asyncio
    async def test_subscribe_handler_no_reply(self, mocker):
        """Test handling when no reply in message."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        service.nats_repository.publish_simple = AsyncMock()
        
        async def test_handler(data: dict) -> dict:
            return {"success": True}
        
        mock_msg = MagicMock(spec=Msg)
        mock_msg.data = b'{"test": "data"}'
        mock_msg.reply = None
        
        await service.subscribe_handler("test.subject", test_handler)
        callback = service.nats_repository.subscribe.call_args[1]["callback"]
        
        await callback(mock_msg)
        
        # Should not publish if no reply
        service.nats_repository.publish_simple.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_subscribe_handler_json_decode(self, mocker):
        """Test JSON decoding from message."""
        service = GameAllocatorService()
        service.nats_repository.subscribe = AsyncMock()
        
        async def test_handler(data: dict) -> dict:
            assert data == {"test": "data"}
            return {"success": True}
        
        mock_msg = MagicMock(spec=Msg)
        mock_msg.data = b'{"test": "data"}'
        mock_msg.reply = None
        
        await service.subscribe_handler("test.subject", test_handler)
        callback = service.nats_repository.subscribe.call_args[1]["callback"]
        
        await callback(mock_msg)


class TestGameAllocatorServiceCreateInstanceRequestHandler:
    """Tests for GameAllocatorService._create_instance_request_handler."""
    
    @pytest.mark.asyncio
    async def test_create_instance_request_handler_success(self, mocker, sample_consul_services):
        """Test successful instance retrieval (returns success=True)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value={
            "address": "192.168.1.10",
            "rest_port": 5002,
            "grpc_port": 50051
        })
        
        handler = service._create_instance_request_handler("game-service")
        result = await handler({"resource_type": "cpu"})
        
        assert result["success"] is True
        assert "instance" in result
    
    @pytest.mark.asyncio
    async def test_create_instance_request_handler_no_instances(self, mocker):
        """Test when no instances available (returns success=False)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, []))
        
        handler = service._create_instance_request_handler("game-service")
        result = await handler({})
        
        assert result["success"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_create_instance_request_handler_resource_type_from_data(self, mocker, sample_consul_services):
        """Test using resource_type from data."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        handler = service._create_instance_request_handler("game-service")
        await handler({"resource_type": "ram"})
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "ram"
    
    @pytest.mark.asyncio
    async def test_create_instance_request_handler_default_cpu(self, mocker, sample_consul_services):
        """Test using 'cpu' as default."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        handler = service._create_instance_request_handler("game-service")
        await handler({})
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "cpu"


class TestGameAllocatorServiceCreateInstancesRequestHandler:
    """Tests for GameAllocatorService._create_instances_request_handler."""
    
    @pytest.mark.asyncio
    async def test_create_instances_request_handler_returns_list(self, mocker, sample_consul_services):
        """Test returning list of all instances."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        
        handler = service._create_instances_request_handler("game-service")
        result = await handler({})
        
        assert result["success"] is True
        assert len(result["instances"]) == 3
    
    @pytest.mark.asyncio
    async def test_create_instances_request_handler_empty_list(self, mocker):
        """Test empty list when no instances."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, []))
        
        handler = service._create_instances_request_handler("game-service")
        result = await handler({})
        
        assert result["success"] is True
        assert result["instances"] == []


class TestGameAllocatorServiceCreateAssignRequestHandler:
    """Tests for GameAllocatorService._create_assign_request_handler."""
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_success(self, mocker, sample_consul_services):
        """Test successful game allocation."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value={
            "address": "192.168.1.10",
            "rest_port": 5002,
            "grpc_port": 50051
        })
        service.cache.set_instance = AsyncMock()
        
        handler = service._create_assign_request_handler("game-service")
        result = await handler({
            "game_id": "game123",
            "settings": {"resource_level": "low"}
        })
        
        assert result["success"] is True
        assert result["instance_id"] == "192.168.1.10"
        service.cache.set_instance.assert_called_once_with("game123", "192.168.1.10")
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_no_game_id(self, mocker):
        """Test when game_id is missing (returns error)."""
        service = GameAllocatorService()
        
        handler = service._create_assign_request_handler("game-service")
        result = await handler({"settings": {}})
        
        assert result["success"] is False
        assert "game_id" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_no_instances(self, mocker):
        """Test when no instances available (returns error)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, []))
        
        handler = service._create_assign_request_handler("game-service")
        result = await handler({"game_id": "game123"})
        
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_saves_to_cache(self, mocker, sample_consul_services):
        """Test saving to cache game_id -> instance_id."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value={
            "address": "192.168.1.10",
            "rest_port": 5002,
            "grpc_port": 50051
        })
        service.cache.set_instance = AsyncMock()
        
        handler = service._create_assign_request_handler("game-service")
        await handler({
            "game_id": "game123",
            "settings": {}
        })
        
        service.cache.set_instance.assert_called_once_with("game123", "192.168.1.10")
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_resource_type_from_settings_low(self, mocker, sample_consul_services):
        """Test determining resource_type from settings (low -> cpu)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        handler = service._create_assign_request_handler("game-service")
        await handler({
            "game_id": "game123",
            "settings": {"resource_level": "low"}
        })
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "cpu"
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_resource_type_from_settings_high(self, mocker, sample_consul_services):
        """Test determining resource_type from settings (high -> ram)."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        handler = service._create_assign_request_handler("game-service")
        await handler({
            "game_id": "game123",
            "settings": {"resource_level": "high"}
        })
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "ram"
    
    @pytest.mark.asyncio
    async def test_create_assign_request_handler_default_cpu(self, mocker, sample_consul_services):
        """Test using 'cpu' as default."""
        service = GameAllocatorService()
        service.consul.health.service = MagicMock(return_value=(None, sample_consul_services))
        service.load_balancer.select_best_instance = AsyncMock(return_value=None)
        
        handler = service._create_assign_request_handler("game-service")
        await handler({
            "game_id": "game123",
            "settings": {}
        })
        
        call_args = service.load_balancer.select_best_instance.call_args
        assert call_args[1]["resource_type"] == "cpu"


class TestGameAllocatorServiceInitializeHandlers:
    """Tests for GameAllocatorService.initialize_handlers."""
    
    @pytest.mark.asyncio
    async def test_initialize_handlers_registers_all_from_config(self, mocker):
        """Test registration of all handlers from SERVICE_CONFIGS."""
        service = GameAllocatorService()
        service.subscribe_handler = AsyncMock()
        
        await service.initialize_handlers()
        
        # Should register handlers for each service config
        assert service.subscribe_handler.call_count >= len(settings.SERVICE_CONFIGS)
    
    @pytest.mark.asyncio
    async def test_initialize_handlers_registers_instance_request(self, mocker):
        """Test registration of instance_request_event."""
        service = GameAllocatorService()
        service.subscribe_handler = AsyncMock()
        
        await service.initialize_handlers()
        
        # Check that instance_request_event handlers were registered
        calls = []
        for call in service.subscribe_handler.call_args_list:
            if call.args:
                calls.append(call.args[0])
            elif call.kwargs:
                calls.append(call.kwargs.get("subject", ""))
        assert any("instance.request" in str(call) for call in calls)
    
    @pytest.mark.asyncio
    async def test_initialize_handlers_registers_instances_request(self, mocker):
        """Test registration of instances_request_event."""
        service = GameAllocatorService()
        service.subscribe_handler = AsyncMock()
        
        await service.initialize_handlers()
        
        calls = []
        for call in service.subscribe_handler.call_args_list:
            if call.args:
                calls.append(call.args[0])
            elif call.kwargs:
                calls.append(call.kwargs.get("subject", ""))
        assert any("instances.request" in str(call) for call in calls)
    
    @pytest.mark.asyncio
    async def test_initialize_handlers_registers_assign_event(self, mocker):
        """Test registration of assign_event."""
        service = GameAllocatorService()
        service.subscribe_handler = AsyncMock()
        
        await service.initialize_handlers()
        
        calls = []
        for call in service.subscribe_handler.call_args_list:
            if call.args:
                calls.append(call.args[0])
            elif call.kwargs:
                calls.append(call.kwargs.get("subject", ""))
        assert any("assign.request" in str(call) for call in calls)
    
    @pytest.mark.asyncio
    async def test_initialize_handlers_skips_missing_events(self, mocker):
        """Test skipping missing events in configuration."""
        service = GameAllocatorService()
        service.subscribe_handler = AsyncMock()
        
        # Mock config with missing event
        original_configs = settings.SERVICE_CONFIGS
        test_config = [{"service_name": "test-service"}]  # No events
        
        with patch('main.settings.SERVICE_CONFIGS', test_config):
            await service.initialize_handlers()
        
        # Should not raise exception


class TestGameAllocatorServiceRun:
    """Tests for GameAllocatorService.run."""
    
    @pytest.mark.asyncio
    async def test_run_initializes_nats(self, mocker):
        """Test NATS connection initialization."""
        service = GameAllocatorService()
        service.nats_repository.get_nc = AsyncMock()
        service.redis_repository.get_redis = AsyncMock()
        service.initialize_handlers = AsyncMock()
        mocker.patch('main.start_healthcheck_server', new_callable=AsyncMock)
        mocker.patch('asyncio.create_task', return_value=MagicMock())
        event_mock = MagicMock()
        # Make wait() wait indefinitely (will be interrupted by timeout)
        # Use a real Event that will never be set
        real_event = asyncio.Event()
        async def wait_forever():
            await real_event.wait()  # This will wait forever since event is never set
        event_mock.wait = wait_forever
        mocker.patch('asyncio.Event', return_value=event_mock)
        
        # Use timeout to prevent infinite wait
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(service.run(), timeout=0.1)
        
        service.nats_repository.get_nc.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_initializes_redis(self, mocker):
        """Test Redis connection initialization."""
        service = GameAllocatorService()
        service.nats_repository.get_nc = AsyncMock()
        service.redis_repository.get_redis = AsyncMock()
        service.initialize_handlers = AsyncMock()
        mocker.patch('main.start_healthcheck_server', new_callable=AsyncMock)
        mocker.patch('asyncio.create_task', return_value=MagicMock())
        event_mock = MagicMock()
        # Make wait() wait indefinitely (will be interrupted by timeout)
        # Use a real Event that will never be set
        real_event = asyncio.Event()
        async def wait_forever():
            await real_event.wait()  # This will wait forever since event is never set
        event_mock.wait = wait_forever
        mocker.patch('asyncio.Event', return_value=event_mock)
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(service.run(), timeout=0.1)
        
        service.redis_repository.get_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_calls_initialize_handlers(self, mocker):
        """Test calling initialize_handlers."""
        service = GameAllocatorService()
        service.nats_repository.get_nc = AsyncMock()
        service.redis_repository.get_redis = AsyncMock()
        service.initialize_handlers = AsyncMock()
        # Mock start_healthcheck_server to return a coroutine that does nothing
        async def mock_start_healthcheck_server(port):
            pass
        start_mock = mocker.patch('main.start_healthcheck_server', side_effect=mock_start_healthcheck_server)
        # Mock create_task to return a simple mock task
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        create_task_mock = mocker.patch('asyncio.create_task', return_value=mock_task)
        event_mock = MagicMock()
        # Make wait() wait indefinitely (will be interrupted by timeout)
        # Use a real Event that will never be set
        real_event = asyncio.Event()
        async def wait_forever():
            await real_event.wait()  # This will wait forever since event is never set
        event_mock.wait = wait_forever
        mocker.patch('asyncio.Event', return_value=event_mock)
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(service.run(), timeout=0.1)
        
        service.initialize_handlers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_starts_healthcheck_server(self, mocker):
        """Test starting healthcheck server."""
        service = GameAllocatorService()
        service.nats_repository.get_nc = AsyncMock()
        service.redis_repository.get_redis = AsyncMock()
        service.initialize_handlers = AsyncMock()
        # Mock start_healthcheck_server to return a coroutine that does nothing
        async def mock_start_healthcheck_server(port):
            pass
        start_mock = mocker.patch('main.start_healthcheck_server', side_effect=mock_start_healthcheck_server)
        # Mock create_task to return a simple mock task
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        create_task_mock = mocker.patch('asyncio.create_task', return_value=mock_task)
        event_mock = MagicMock()
        # Make wait() wait indefinitely (will be interrupted by timeout)
        # Use a real Event that will never be set
        real_event = asyncio.Event()
        async def wait_forever():
            await real_event.wait()  # This will wait forever since event is never set
        event_mock.wait = wait_forever
        mocker.patch('asyncio.Event', return_value=event_mock)
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(service.run(), timeout=0.1)
        
        # start_healthcheck_server should be called via create_task
        create_task_mock.assert_called_once()
        # Check that start_healthcheck_server was passed to create_task
        call_args = create_task_mock.call_args
        assert call_args is not None


class TestHealthCheckHandler:
    """Tests for health_check_handler."""
    
    @pytest.mark.asyncio
    async def test_health_check_handler_returns_json(self):
        """Test returning correct JSON response."""
        mock_request = MagicMock()
        
        response = await health_check_handler(mock_request)
        
        assert response.status == 200
        # Check response body - aiohttp Response has text property, need to parse JSON
        import json
        body = json.loads(response.text)
        assert body["status"] == "healthy"
        assert body["service"] == settings.SERVICE_NAME


class TestCreateHealthcheckServer:
    """Tests for create_healthcheck_server."""
    
    def test_create_healthcheck_server_creates_app(self):
        """Test creating aiohttp Application."""
        app = create_healthcheck_server()
        
        assert app is not None
    
    def test_create_healthcheck_server_registers_health_endpoint(self):
        """Test registration of /health endpoint."""
        app = create_healthcheck_server()
        
        # Check that route exists - check resource if available
        routes = []
        for route in app.router.routes():
            if hasattr(route, 'resource'):
                resource = route.resource
                if hasattr(resource, 'canonical'):
                    routes.append(resource.canonical)
                elif hasattr(resource, '_path'):
                    routes.append(resource._path)
            elif hasattr(route, 'path'):
                routes.append(route.path)
            elif hasattr(route, '_path'):
                routes.append(route._path)
        
        route_strings = [str(route) for route in routes]
        assert any("/health" in route_str for route_str in route_strings)


class TestStartHealthcheckServer:
    """Tests for start_healthcheck_server."""
    
    @pytest.mark.asyncio
    async def test_start_healthcheck_server_runs_on_port(self, mocker):
        """Test server starts on correct port."""
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock()
        mock_site = MagicMock()
        mock_site.start = AsyncMock()
        
        app_runner_mock = mocker.patch('aiohttp.web.AppRunner', return_value=mock_runner)
        tcp_site_mock = mocker.patch('aiohttp.web.TCPSite', return_value=mock_site)
        
        await start_healthcheck_server(port=5005)
        
        tcp_site_mock.assert_called_once()
        call_args = tcp_site_mock.call_args
        assert call_args[0][1] == "0.0.0.0"
        assert call_args[0][2] == 5005


class TestRegisterService:
    """Tests for register_service."""
    
    def test_register_service_registers_in_consul(self, mocker):
        """Test registration in Consul with correct parameters."""
        consul_mock = mocker.patch('main.consul.Consul')
        mock_consul_instance = MagicMock()
        consul_mock.return_value = mock_consul_instance
        
        register_service()
        
        mock_consul_instance.agent.service.register.assert_called_once()
        call_args = mock_consul_instance.agent.service.register.call_args
        assert call_args[1]["name"] == settings.SERVICE_NAME
    
    def test_register_service_uses_hostname(self, mocker):
        """Test using hostname for service_id."""
        consul_mock = mocker.patch('main.consul.Consul')
        mock_consul_instance = MagicMock()
        consul_mock.return_value = mock_consul_instance
        mocker.patch('socket.gethostname', return_value="test-host")
        
        register_service()
        
        call_args = mock_consul_instance.agent.service.register.call_args
        assert "test-host" in call_args[1]["service_id"]
    
    def test_register_service_http_healthcheck(self, mocker):
        """Test HTTP healthcheck setup."""
        consul_mock = mocker.patch('main.consul.Consul')
        mock_consul_instance = MagicMock()
        consul_mock.return_value = mock_consul_instance
        mocker.patch('socket.gethostname', return_value="test-host")
        
        register_service()
        
        call_args = mock_consul_instance.agent.service.register.call_args
        assert call_args[1]["check"] is not None
    
    def test_register_service_correct_tags_and_port(self, mocker):
        """Test correct tags and port."""
        consul_mock = mocker.patch('main.consul.Consul')
        mock_consul_instance = MagicMock()
        consul_mock.return_value = mock_consul_instance
        
        register_service()
        
        call_args = mock_consul_instance.agent.service.register.call_args
        assert "traefik" in call_args[1]["tags"]
        assert call_args[1]["port"] == settings.PORT

