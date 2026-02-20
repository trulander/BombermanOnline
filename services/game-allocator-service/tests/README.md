# Tests for game-allocator-service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Common fixtures and mocks
├── test_load_balancer.py    # LoadBalancer tests
├── test_game_allocator_service.py  # GameAllocatorService tests
├── test_nats_repository.py   # NatsRepository tests
├── test_redis_repository.py  # RedisRepository tests
├── test_game_cache.py       # GameInstanceCache tests
├── test_main.py             # Helper functions tests
├── test_integration.py      # Integration tests
└── test_config.py           # Configuration tests
```

## Running Tests

### Installing Dependencies

```bash
cd services/game-allocator-service
uv sync --group dev
```

### Running All Tests

```bash
uv run pytest
```

### Running with Code Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

### Running a Specific Test File

```bash
uv run pytest tests/test_load_balancer.py
```

### Running a Specific Test

```bash
uv run pytest tests/test_load_balancer.py::TestLoadBalancerInit::test_init_with_correct_parameters
```

## Code Coverage

Target: **>90% code coverage**

Current coverage: **99%** (3 lines in `main.py` entry point are not covered, which is normal practice).

To view the coverage report after running with `--cov-report=html`:

```bash
open htmlcov/index.html  # macOS/Linux
```

## Test Types

### Unit Tests
- `test_load_balancer.py` - LoadBalancer tests
- `test_nats_repository.py` - NatsRepository tests
- `test_redis_repository.py` - RedisRepository tests
- `test_game_cache.py` - GameInstanceCache tests
- `test_main.py` - Helper functions tests
- `test_config.py` - Configuration tests
- `test_logging_config.py` - Logging configuration tests

### Integration Tests
- `test_integration.py` - Component interaction tests
- `test_game_allocator_service.py` - GameAllocatorService tests with dependencies

## Fixtures

All common fixtures are located in `conftest.py`:
- `mock_consul_client` - Mock Consul client
- `mock_prometheus_client` - Mock Prometheus client
- `load_balancer` - LoadBalancer instance with mocks
- `nats_repository` - NatsRepository instance with mocks
- `redis_repository` - RedisRepository instance with fake Redis
- `game_cache` - GameInstanceCache instance
- `sample_consul_services` - Sample Consul service data
- `sample_instance_loads` - Sample instance load data
- `sample_equal_load_instances` - Sample equal load instances

## Mocks and Fixtures

Tests use:
- **unittest.mock** for mocking external dependencies
- **fakeredis** for testing Redis without a real server
- **pytest-mock** for additional mocking capabilities
- **pytest-asyncio** for asynchronous tests
- **pytest-cov** for code coverage analysis
