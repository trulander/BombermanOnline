from enum import Enum


class GameStatus(Enum):
    """Статусы игры"""
    PENDING = "pending"        # Ожидание игроков
    STARTING = "starting"      # Подготовка к запуску
    ACTIVE = "active"          # Активная игра
    PAUSED = "paused"          # Приостановлена
    FINISHED = "finished"      # Завершена 