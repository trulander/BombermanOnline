from enum import Enum


class GameModeType(Enum):
    """Типы игровых режимов"""
    CAMPAIGN = "campaign"                 # Прохождение с возможностью кооператива
    FREE_FOR_ALL = "free_for_all"         # Все против всех (количество игроков = количество команд)
    CAPTURE_THE_FLAG = "capture_the_flag"  # Командная игра с флагами


