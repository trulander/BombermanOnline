from enum import Enum


class GameModeType(Enum):
    """Типы игровых режимов"""
    CAMPAIGN = "CAMPAIGN"                 # Прохождение с возможностью кооператива
    FREE_FOR_ALL = "FREE_FOR_ALL"         # Все против всех (количество игроков = количество команд)
    CAPTURE_THE_FLAG = "CAPTURE_THE_FLAG" # Командная игра с флагами
    TRAINING_IA = "TRAINING_IA"           # Режим для тренеровки ai моделей, в изолированном режиме без замкнутого игрового цикла.


