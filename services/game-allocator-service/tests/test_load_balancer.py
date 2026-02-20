"""
Tests for LoadBalancer class.
"""
import asyncio
import pytest
from unittest.mock import MagicMock

from load_balancer import LoadBalancer


class TestLoadBalancerInit:
    """Tests for LoadBalancer.__init__."""
    
    def test_init_with_correct_parameters(self, mock_consul_client, mock_prometheus_client):
        """Test initialization with correct parameters."""
        lb = LoadBalancer(
            consul_client=mock_consul_client,
            prometheus_client=mock_prometheus_client,
            load_threshold=2.0
        )
        assert lb.consul == mock_consul_client
        assert lb.prom == mock_prometheus_client
        assert lb.load_threshold == 2.0
    
    def test_init_load_threshold_set(self, mock_consul_client, mock_prometheus_client):
        """Test that load_threshold is set correctly."""
        lb = LoadBalancer(
            consul_client=mock_consul_client,
            prometheus_client=mock_prometheus_client,
            load_threshold=5.0
        )
        assert lb.load_threshold == 5.0
    
    def test_init_rotation_state_and_lock(self, mock_consul_client, mock_prometheus_client):
        """Test initialization of _rotation_state and _rotation_lock."""
        lb = LoadBalancer(
            consul_client=mock_consul_client,
            prometheus_client=mock_prometheus_client,
            load_threshold=2.0
        )
        assert isinstance(lb._rotation_state, dict)
        assert lb._rotation_state == {}
        assert lb._rotation_lock is not None


class TestLoadBalancerGetInstanceLoad:
    """Tests for LoadBalancer.get_instance_load."""
    
    def test_get_instance_load_success(self, load_balancer):
        """Test successful retrieval of CPU and RAM metrics."""
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.5"]}],  # CPU result
            [{"value": [None, "1024000"]}]  # RAM result
        ])
        
        result = load_balancer.get_instance_load(
            service_name="game-service",
            instance_id="instance-1",
            address="192.168.1.10"
        )
        
        assert result["instance_id"] == "instance-1"
        assert result["cpu_usage"] == 10.5
        assert result["ram_usage"] == 1024000.0
        assert result["address"] == "192.168.1.10"
        assert load_balancer.prom.custom_query.call_count == 2
    
    def test_get_instance_load_no_prometheus_data(self, load_balancer):
        """Test handling of missing Prometheus data (returns 0.0)."""
        load_balancer.prom.custom_query = MagicMock(return_value=[])
        
        result = load_balancer.get_instance_load(
            service_name="game-service",
            instance_id="instance-1",
            address="192.168.1.10"
        )
        
        assert result["cpu_usage"] == 0.0
        assert result["ram_usage"] == 0.0
    
    def test_get_instance_load_cpu_exception(self, load_balancer):
        """Test handling of exceptions when querying CPU metrics."""
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            Exception("Prometheus error"),  # CPU query fails
            [{"value": [None, "1024000"]}]  # RAM query succeeds
        ])
        
        result = load_balancer.get_instance_load(
            service_name="game-service",
            instance_id="instance-1",
            address="192.168.1.10"
        )
        
        assert result["cpu_usage"] == 0.0
        assert result["ram_usage"] == 1024000.0
    
    def test_get_instance_load_ram_exception(self, load_balancer):
        """Test handling of exceptions when querying RAM metrics."""
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.5"]}],  # CPU query succeeds
            Exception("Prometheus error")  # RAM query fails
        ])
        
        result = load_balancer.get_instance_load(
            service_name="game-service",
            instance_id="instance-1",
            address="192.168.1.10"
        )
        
        assert result["cpu_usage"] == 10.5
        assert result["ram_usage"] == 0.0
    
    def test_get_instance_load_promql_query_format(self, load_balancer):
        """Test that PromQL queries are correctly formatted with service_name."""
        load_balancer.prom.custom_query = MagicMock(return_value=[])
        
        load_balancer.get_instance_load(
            service_name="ai-service",
            instance_id="instance-1",
            address="192.168.1.20"
        )
        
        # Check that custom_query was called with correct PromQL
        calls = load_balancer.prom.custom_query.call_args_list
        cpu_query = calls[0][0][0]
        ram_query = calls[1][0][0]
        
        assert "ai-service" in cpu_query
        assert "192.168.1.20" in cpu_query
        assert "ai-service" in ram_query
        assert "192.168.1.20" in ram_query
    
    def test_get_instance_load_return_structure(self, load_balancer):
        """Test that returned data has correct structure."""
        load_balancer.prom.custom_query = MagicMock(return_value=[])
        
        result = load_balancer.get_instance_load(
            service_name="game-service",
            instance_id="instance-1",
            address="192.168.1.10"
        )
        
        assert "instance_id" in result
        assert "cpu_usage" in result
        assert "ram_usage" in result
        assert "address" in result


class TestLoadBalancerFindEqualLoadInstances:
    """Tests for LoadBalancer.find_equal_load_instances."""
    
    def test_find_equal_load_instances_empty_list(self, load_balancer):
        """Test with empty instance list (returns [])."""
        result = load_balancer.find_equal_load_instances([], "cpu")
        assert result == []
    
    def test_find_equal_load_instances_single_instance(self, load_balancer, sample_instance_loads):
        """Test with single instance (returns that instance)."""
        single_load = [sample_instance_loads[0]]
        result = load_balancer.find_equal_load_instances(single_load, "cpu")
        assert len(result) == 1
        assert result[0] == single_load[0]
    
    def test_find_equal_load_instances_different_loads_within_threshold(self, load_balancer):
        """Test with instances having different loads within threshold."""
        instance_loads = [
            {"cpu_usage": 10.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 11.5, "ram_usage": 2000.0, "address": "addr2"},  # Within threshold (10 + 2 = 12)
            {"cpu_usage": 15.0, "ram_usage": 3000.0, "address": "addr3"}  # Outside threshold
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert len(result) == 2
        assert result[0]["address"] == "addr1"
        assert result[1]["address"] == "addr2"
    
    def test_find_equal_load_instances_all_within_threshold(self, load_balancer):
        """Test with all instances within threshold (returns all)."""
        instance_loads = [
            {"cpu_usage": 10.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 11.0, "ram_usage": 2000.0, "address": "addr2"},
            {"cpu_usage": 11.5, "ram_usage": 3000.0, "address": "addr3"}
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert len(result) == 3
    
    def test_find_equal_load_instances_some_within_threshold(self, load_balancer):
        """Test with some instances within threshold (returns only those)."""
        instance_loads = [
            {"cpu_usage": 10.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 11.0, "ram_usage": 2000.0, "address": "addr2"},
            {"cpu_usage": 20.0, "ram_usage": 3000.0, "address": "addr3"}  # Outside threshold
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert len(result) == 2
        assert all(inst["address"] in ["addr1", "addr2"] for inst in result)
    
    def test_find_equal_load_instances_resource_type_cpu(self, load_balancer):
        """Test with resource_type='cpu'."""
        instance_loads = [
            {"cpu_usage": 10.0, "ram_usage": 5000.0, "address": "addr1"},
            {"cpu_usage": 11.5, "ram_usage": 1000.0, "address": "addr2"},  # Lower RAM but within CPU threshold
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert len(result) == 2
    
    def test_find_equal_load_instances_resource_type_ram(self, load_balancer):
        """Test with resource_type='ram'."""
        instance_loads = [
            {"cpu_usage": 50.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 10.0, "ram_usage": 1001.0, "address": "addr2"},  # Within RAM threshold (1000 + 2.0 = 1002)
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "ram")
        
        assert len(result) == 2
    
    def test_find_equal_load_instances_sorted_by_load(self, load_balancer):
        """Test that instances are sorted by load."""
        instance_loads = [
            {"cpu_usage": 15.0, "ram_usage": 3000.0, "address": "addr3"},
            {"cpu_usage": 10.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 12.0, "ram_usage": 2000.0, "address": "addr2"},
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert result[0]["cpu_usage"] == 10.0
        assert result[1]["cpu_usage"] == 12.0
    
    def test_find_equal_load_instances_threshold_calculation(self, load_balancer):
        """Test correct threshold calculation (min_load + threshold)."""
        instance_loads = [
            {"cpu_usage": 10.0, "ram_usage": 1000.0, "address": "addr1"},
            {"cpu_usage": 12.0, "ram_usage": 2000.0, "address": "addr2"},  # Exactly at threshold (10 + 2)
            {"cpu_usage": 12.1, "ram_usage": 3000.0, "address": "addr3"}  # Just above threshold
        ]
        
        result = load_balancer.find_equal_load_instances(instance_loads, "cpu")
        
        assert len(result) == 2
        assert result[0]["address"] == "addr1"
        assert result[1]["address"] == "addr2"


class TestLoadBalancerSelectInstanceWithRotation:
    """Tests for LoadBalancer.select_instance_with_rotation."""
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_single_instance(self, load_balancer, sample_equal_load_instances):
        """Test with single instance (returns without rotation)."""
        single_instance = [sample_equal_load_instances[0]]
        result = await load_balancer.select_instance_with_rotation(
            service_name="game-service",
            equal_load_instances=single_instance,
            resource_type="cpu"
        )
        
        assert result == single_instance[0]
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_multiple_instances(self, load_balancer, sample_equal_load_instances):
        """Test with multiple instances (round-robin rotation)."""
        result1 = await load_balancer.select_instance_with_rotation(
            service_name="game-service",
            equal_load_instances=sample_equal_load_instances,
            resource_type="cpu"
        )
        
        result2 = await load_balancer.select_instance_with_rotation(
            service_name="game-service",
            equal_load_instances=sample_equal_load_instances,
            resource_type="cpu"
        )
        
        # Should rotate between instances
        assert result1["address"] != result2["address"]
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_sequence(self, load_balancer):
        """Test rotation sequence (A->B->C->A)."""
        instances = [
            {"address": "addr1", "cpu_usage": 10.0, "ram_usage": 1000.0},
            {"address": "addr2", "cpu_usage": 11.0, "ram_usage": 2000.0},
            {"address": "addr3", "cpu_usage": 12.0, "ram_usage": 3000.0},
        ]
        
        results = []
        for _ in range(4):  # Request 4 times to test wrap-around
            result = await load_balancer.select_instance_with_rotation(
                service_name="game-service",
                equal_load_instances=instances,
                resource_type="cpu"
            )
            results.append(result["address"])
        
        # Should cycle: addr1 -> addr2 -> addr3 -> addr1
        assert results[0] == "addr1"
        assert results[1] == "addr2"
        assert results[2] == "addr3"
        assert results[3] == "addr1"  # Wrap-around
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_wrap_around(self, load_balancer, sample_equal_load_instances):
        """Test wrap-around after last instance."""
        # Request instances multiple times to test wrap-around
        addresses = []
        for _ in range(len(sample_equal_load_instances) + 1):
            result = await load_balancer.select_instance_with_rotation(
                service_name="game-service",
                equal_load_instances=sample_equal_load_instances,
                resource_type="cpu"
            )
            addresses.append(result["address"])
        
        # Last should wrap to first
        assert addresses[-1] == addresses[0]
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_key_generation(self, load_balancer, sample_equal_load_instances):
        """Test correct rotation key generation."""
        await load_balancer.select_instance_with_rotation(
            service_name="game-service",
            equal_load_instances=sample_equal_load_instances,
            resource_type="cpu"
        )
        
        # Check that rotation key was created
        addresses = sorted([inst["address"] for inst in sample_equal_load_instances])
        expected_key = f"game-service:cpu:{','.join(addresses)}"
        assert expected_key in load_balancer._rotation_state
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_thread_safety(self, load_balancer):
        """Test thread-safety with multiple parallel requests."""
        instances = [
            {"address": "addr1", "cpu_usage": 10.0, "ram_usage": 1000.0},
            {"address": "addr2", "cpu_usage": 11.0, "ram_usage": 2000.0},
        ]
        
        # Make multiple parallel requests
        tasks = [
            load_balancer.select_instance_with_rotation(
                service_name="game-service",
                equal_load_instances=instances,
                resource_type="cpu"
            )
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        addresses = [r["address"] for r in results]
        
        # All results should be valid addresses
        assert all(addr in ["addr1", "addr2"] for addr in addresses)
        # Rotation state should be updated correctly (10 requests, modulo 2 = 0)
        key = "game-service:cpu:addr1,addr2"
        assert key in load_balancer._rotation_state
        assert load_balancer._rotation_state[key] == 0  # 10 % 2 = 0
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_empty_list(self, load_balancer):
        """Test exception when empty list is provided."""
        with pytest.raises(ValueError, match="equal_load_instances cannot be empty"):
            await load_balancer.select_instance_with_rotation(
                service_name="game-service",
                equal_load_instances=[],
                resource_type="cpu"
            )
    
    @pytest.mark.asyncio
    async def test_select_instance_with_rotation_different_keys(self, load_balancer):
        """Test that different service_name and resource_type create different keys."""
        # Need multiple instances to trigger rotation (single instance doesn't create rotation key)
        instances1 = [
            {"address": "addr1", "cpu_usage": 10.0, "ram_usage": 1000.0},
            {"address": "addr2", "cpu_usage": 11.0, "ram_usage": 2000.0},
        ]
        instances2 = [
            {"address": "addr1", "cpu_usage": 10.0, "ram_usage": 1000.0},
            {"address": "addr2", "cpu_usage": 11.0, "ram_usage": 2000.0},
        ]
        
        await load_balancer.select_instance_with_rotation(
            service_name="game-service",
            equal_load_instances=instances1,
            resource_type="cpu"
        )
        
        await load_balancer.select_instance_with_rotation(
            service_name="ai-service",
            equal_load_instances=instances2,
            resource_type="cpu"
        )
        
        # Should have different keys (key format: service_name:resource_type:sorted_addresses)
        assert "game-service:cpu:addr1,addr2" in load_balancer._rotation_state
        assert "ai-service:cpu:addr1,addr2" in load_balancer._rotation_state


class TestLoadBalancerSelectBestInstance:
    """Tests for LoadBalancer.select_best_instance."""
    
    @pytest.mark.asyncio
    async def test_select_best_instance_empty_list(self, load_balancer):
        """Test with empty instances list (returns None)."""
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=[],
            resource_type="cpu"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_select_best_instance_single_instance(self, load_balancer, sample_consul_services):
        """Test with single instance (returns without load check)."""
        single_instance = [sample_consul_services[0]]
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=single_instance,
            resource_type="cpu"
        )
        
        assert result is not None
        assert result["address"] == "192.168.1.10"
        assert result["rest_port"] == 5002
        assert result["grpc_port"] == 50051
        # Should not call Prometheus for single instance
        assert load_balancer.prom.custom_query.call_count == 0
    
    @pytest.mark.asyncio
    async def test_select_best_instance_different_loads(self, load_balancer, sample_consul_services):
        """Test with instances having different loads (selects least loaded)."""
        # Mock Prometheus responses - first instance has lowest load
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU for instance 1
            [{"value": [None, "1024"]}],  # RAM for instance 1
            [{"value": [None, "20.0"]}],  # CPU for instance 2
            [{"value": [None, "2048"]}],  # RAM for instance 2
            [{"value": [None, "30.0"]}],  # CPU for instance 3
            [{"value": [None, "3072"]}],  # RAM for instance 3
        ])
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services,
            resource_type="cpu"
        )
        
        # Should select instance with lowest CPU (10.0)
        assert result["address"] == "192.168.1.10"
    
    @pytest.mark.asyncio
    async def test_select_best_instance_equal_loads_round_robin(self, load_balancer, sample_consul_services):
        """Test with equally loaded instances (uses round-robin)."""
        # Mock Prometheus responses - all instances have similar load
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU for instance 1
            [{"value": [None, "1024"]}],  # RAM for instance 1
            [{"value": [None, "11.0"]}],  # CPU for instance 2 (within threshold)
            [{"value": [None, "2048"]}],  # RAM for instance 2
            [{"value": [None, "11.5"]}],  # CPU for instance 3 (within threshold)
            [{"value": [None, "3072"]}],  # RAM for instance 3
        ])
        
        result1 = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services,
            resource_type="cpu"
        )
        
        result2 = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services,
            resource_type="cpu"
        )
        
        # Should use round-robin, so results might differ
        assert result1 is not None
        assert result2 is not None
    
    @pytest.mark.asyncio
    async def test_select_best_instance_extract_ports(self, load_balancer, sample_consul_services):
        """Test correct extraction of rest_port and grpc_port from Meta."""
        single_instance = [sample_consul_services[0]]
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=single_instance,
            resource_type="cpu"
        )
        
        assert result["rest_port"] == 5002
        assert result["grpc_port"] == 50051
    
    @pytest.mark.asyncio
    async def test_select_best_instance_no_meta(self, load_balancer):
        """Test handling of missing Meta in Service."""
        instance_without_meta = [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10"
            }
        }]
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=instance_without_meta,
            resource_type="cpu"
        )
        
        assert result["rest_port"] == 0
        assert result["grpc_port"] == 0
    
    @pytest.mark.asyncio
    async def test_select_best_instance_no_ports_in_meta(self, load_balancer):
        """Test handling of missing ports in Meta."""
        instance_without_ports = [{
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10",
                "Meta": {}
            }
        }]
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=instance_without_ports,
            resource_type="cpu"
        )
        
        assert result["rest_port"] == 0
        assert result["grpc_port"] == 0
    
    @pytest.mark.asyncio
    async def test_select_best_instance_fallback_address_not_found(self, load_balancer, sample_consul_services):
        """Test fallback when selected address not found in instances."""
        # Need multiple instances to trigger load checking (single instance returns directly)
        test_instances = sample_consul_services[:2]
        
        # Mock Prometheus to return load data for both instances
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU for instance 1
            [{"value": [None, "1024"]}],  # RAM for instance 1
            [{"value": [None, "11.0"]}],  # CPU for instance 2
            [{"value": [None, "2048"]}],  # RAM for instance 2
        ])
        
        # Mock get_instance_load to return address that doesn't match Service.Address for first instance
        call_count = [0]
        def mock_get_load(service_name, instance_id, address):
            call_count[0] += 1
            # For first call, return address different from Service.Address
            if call_count[0] == 1:
                return {
                    "instance_id": instance_id,
                    "cpu_usage": 10.0,
                    "ram_usage": 1024.0,
                    "address": "unknown-address"  # Different from actual instance address (192.168.1.10)
                }
            else:
                # For second call, return normal address
                return {
                    "instance_id": instance_id,
                    "cpu_usage": 11.0,
                    "ram_usage": 2048.0,
                    "address": address  # Normal address
                }
        
        load_balancer.get_instance_load = MagicMock(side_effect=mock_get_load)
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=test_instances,
            resource_type="cpu"
        )
        
        # Should return fallback with address but ports = 0
        # The selected address from get_instance_load doesn't match Service.Address
        assert result["address"] == "unknown-address"
        assert result["rest_port"] == 0
        assert result["grpc_port"] == 0
    
    @pytest.mark.asyncio
    async def test_select_best_instance_resource_type_cpu(self, load_balancer, sample_consul_services):
        """Test with resource_type='cpu'."""
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU
            [{"value": [None, "5000"]}],  # RAM
            [{"value": [None, "20.0"]}],  # CPU
            [{"value": [None, "1000"]}],  # RAM (lower but CPU is higher)
        ])
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services[:2],
            resource_type="cpu"
        )
        
        # Should select based on CPU, not RAM
        assert result["address"] == "192.168.1.10"
    
    @pytest.mark.asyncio
    async def test_select_best_instance_resource_type_ram(self, load_balancer, sample_consul_services):
        """Test with resource_type='ram'."""
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "50.0"]}],  # CPU (higher)
            [{"value": [None, "1000"]}],  # RAM (lower)
            [{"value": [None, "10.0"]}],  # CPU (lower)
            [{"value": [None, "5000"]}],  # RAM (higher)
        ])
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services[:2],
            resource_type="ram"
        )
        
        # Should select based on RAM, not CPU
        assert result["address"] == "192.168.1.10"
    
    @pytest.mark.asyncio
    async def test_select_best_instance_no_equal_load_instances(self, load_balancer, sample_consul_services):
        """Test when no equal load instances found (all have very different loads)."""
        # Mock Prometheus responses - all instances have very different loads
        # Note: find_equal_load_instances always returns at least the minimum load instance
        # To trigger the "no equal load" case, we need to mock find_equal_load_instances to return empty list
        load_balancer.prom.custom_query = MagicMock(side_effect=[
            [{"value": [None, "10.0"]}],  # CPU for instance 1
            [{"value": [None, "1024"]}],  # RAM for instance 1
            [{"value": [None, "50.0"]}],  # CPU for instance 2
            [{"value": [None, "2048"]}],  # RAM for instance 2
            [{"value": [None, "100.0"]}],  # CPU for instance 3
            [{"value": [None, "3072"]}],  # RAM for instance 3
        ])
        
        # Mock find_equal_load_instances to return empty list to test the None return case
        original_find = load_balancer.find_equal_load_instances
        load_balancer.find_equal_load_instances = MagicMock(return_value=[])
        
        result = await load_balancer.select_best_instance(
            service_name="game-service",
            instances=sample_consul_services,
            resource_type="cpu"
        )
        
        # Should return None when no equal load instances found
        assert result is None

