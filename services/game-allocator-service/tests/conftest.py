"""
Common fixtures and mocks for game-allocator-service tests.
"""
import sys
from pathlib import Path

# Add app directory to path to allow imports
project_root = Path(__file__).parent.parent
app_dir = project_root / "app"
sys.path.insert(0, str(app_dir))

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import fakeredis
import numpy as np
import pytest
from prometheus_api_client import PrometheusConnect

from config import settings
from load_balancer import LoadBalancer
from nats_repository import NatsRepository
from redis_repository import RedisRepository
from game_cache import GameInstanceCache
import consul


@pytest.fixture
def mock_consul_client():
    """Mock Consul client."""
    mock_consul = MagicMock(spec=consul.Consul)
    mock_consul.health = MagicMock()
    mock_consul.agent = MagicMock()
    return mock_consul


@pytest.fixture
def mock_prometheus_client():
    """Mock Prometheus client."""
    mock_prom = MagicMock(spec=PrometheusConnect)
    return mock_prom


@pytest.fixture
def load_balancer(mock_consul_client, mock_prometheus_client):
    """Create LoadBalancer instance with mocked dependencies."""
    return LoadBalancer(
        consul_client=mock_consul_client,
        prometheus_client=mock_prometheus_client,
        load_threshold=2.0
    )


@pytest.fixture
def mock_nats_client():
    """Mock NATS client."""
    mock_nc = AsyncMock()
    mock_nc.is_closed = False
    mock_nc.is_connected = True
    mock_nc.publish = AsyncMock(return_value=None)
    mock_nc.subscribe = AsyncMock(return_value=None)
    mock_nc.drain = AsyncMock(return_value=None)
    return mock_nc


@pytest.fixture
def nats_repository(mocker):
    """Create NatsRepository instance with mocked NATS connection."""
    repo = NatsRepository()
    mock_nc = AsyncMock()
    mock_nc.is_closed = False
    mock_nc.is_connected = True
    mock_nc.publish = AsyncMock(return_value=None)
    mock_nc.subscribe = AsyncMock(return_value=None)
    mock_nc.drain = AsyncMock(return_value=None)
    
    # Mock nats.connect
    mocker.patch('nats_repository.nats.connect', return_value=mock_nc)
    repo._nc = mock_nc
    return repo


@pytest.fixture
def fake_redis_server():
    """Create fake Redis server for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
async def redis_repository(fake_redis_server, mocker):
    """Create RedisRepository instance with fake Redis."""
    repo = RedisRepository()
    # Mock redis.Redis to return fake server
    mocker.patch('redis_repository.redis.Redis', return_value=fake_redis_server)
    repo._redis = fake_redis_server
    return repo


@pytest.fixture
async def game_cache(redis_repository):
    """Create GameInstanceCache instance."""
    return GameInstanceCache(redis_repository=redis_repository, ttl=60)


@pytest.fixture
def sample_consul_services():
    """Sample Consul service instances for testing."""
    return [
        {
            "Service": {
                "ID": "game-service-1",
                "Address": "192.168.1.10",
                "Meta": {
                    "rest_api_port": "5002",
                    "grpc_port": "50051"
                }
            }
        },
        {
            "Service": {
                "ID": "game-service-2",
                "Address": "192.168.1.11",
                "Meta": {
                    "rest_api_port": "5002",
                    "grpc_port": "50051"
                }
            }
        },
        {
            "Service": {
                "ID": "game-service-3",
                "Address": "192.168.1.12",
                "Meta": {
                    "rest_api_port": "5002",
                    "grpc_port": "50051"
                }
            }
        }
    ]


@pytest.fixture
def sample_instance_loads():
    """Sample instance load data for testing."""
    return [
        {
            "instance_id": "game-service-1",
            "cpu_usage": 10.0,
            "ram_usage": 1024.0,
            "address": "192.168.1.10"
        },
        {
            "instance_id": "game-service-2",
            "cpu_usage": 12.0,
            "ram_usage": 2048.0,
            "address": "192.168.1.11"
        },
        {
            "instance_id": "game-service-3",
            "cpu_usage": 15.0,
            "ram_usage": 3072.0,
            "address": "192.168.1.12"
        }
    ]


@pytest.fixture
def sample_equal_load_instances():
    """Sample equally loaded instances for testing."""
    return [
        {
            "instance_id": "game-service-1",
            "cpu_usage": 10.0,
            "ram_usage": 1024.0,
            "address": "192.168.1.10"
        },
        {
            "instance_id": "game-service-2",
            "cpu_usage": 11.0,
            "ram_usage": 2048.0,
            "address": "192.168.1.11"
        }
    ]


@pytest.fixture
def numpy_integer():
    """Sample numpy integer for testing."""
    return np.int64(42)


@pytest.fixture
def numpy_float():
    """Sample numpy float for testing."""
    return np.float64(3.14)


@pytest.fixture
def numpy_array():
    """Sample numpy array for testing."""
    return np.array([1, 2, 3, 4, 5])


# Event loop fixture removed - pytest-asyncio handles it automatically with asyncio_mode = auto

