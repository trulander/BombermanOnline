from enum import Enum


class GameStatus(Enum):
    """Статусы игры"""
    PENDING = "pending"        # Ожидание игроков
    ACTIVE = "active"          # Активная игра
    PAUSED = "paused"          # Приостановлена
    FINISHED = "finished"      # Завершена 