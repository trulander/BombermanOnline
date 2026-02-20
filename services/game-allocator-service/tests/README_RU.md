# Тесты для game-allocator-service
[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Общие фикстуры и моки
├── test_load_balancer.py    # Тесты LoadBalancer
├── test_game_allocator_service.py  # Тесты GameAllocatorService
├── test_nats_repository.py   # Тесты NatsRepository
├── test_redis_repository.py  # Тесты RedisRepository
├── test_game_cache.py       # Тесты GameInstanceCache
├── test_main.py             # Тесты вспомогательных функций
├── test_integration.py      # Интеграционные тесты
└── test_config.py           # Тесты конфигурации
```

## Запуск тестов

### Установка зависимостей

```bash
cd services/game-allocator-service
uv sync --group dev
```

### Запуск всех тестов

```bash
uv run pytest
```

### Запуск с покрытием кода

```bash
uv run pytest --cov=app --cov-report=html
```

### Запуск конкретного файла тестов

```bash
uv run pytest tests/test_load_balancer.py
```

### Запуск конкретного теста

```bash
uv run pytest tests/test_load_balancer.py::TestLoadBalancerInit::test_init_with_correct_parameters
```

## Покрытие кода

Цель: **>90% покрытия кода тестами**

Текущее покрытие: **99%** (3 строки в точке входа `main.py` не покрыты, что является нормальной практикой).

Для просмотра отчета о покрытии после запуска с `--cov-report=html`:

```bash
open htmlcov/index.html  # macOS/Linux
```

## Типы тестов

### Unit тесты
- `test_load_balancer.py` - тесты LoadBalancer
- `test_nats_repository.py` - тесты NatsRepository
- `test_redis_repository.py` - тесты RedisRepository
- `test_game_cache.py` - тесты GameInstanceCache
- `test_main.py` - тесты вспомогательных функций
- `test_config.py` - тесты конфигурации
- `test_logging_config.py` - тесты конфигурации логирования

### Интеграционные тесты
- `test_integration.py` - тесты взаимодействия компонентов
- `test_game_allocator_service.py` - тесты GameAllocatorService с зависимостями

## Фикстуры

Все общие фикстуры находятся в `conftest.py`:
- `mock_consul_client` - мок Consul клиента
- `mock_prometheus_client` - мок Prometheus клиента
- `load_balancer` - экземпляр LoadBalancer с моками
- `nats_repository` - экземпляр NatsRepository с моками
- `redis_repository` - экземпляр RedisRepository с fake Redis
- `game_cache` - экземпляр GameInstanceCache
- `sample_consul_services` - примеры данных Consul сервисов
- `sample_instance_loads` - примеры данных нагрузки инстансов
- `sample_equal_load_instances` - примеры равнонагруженных инстансов

## Моки и фикстуры

Тесты используют:
- **unittest.mock** для моков внешних зависимостей
- **fakeredis** для тестирования Redis без реального сервера
- **pytest-mock** для дополнительных возможностей моков
- **pytest-asyncio** для асинхронных тестов
- **pytest-cov** для анализа покрытия кода
