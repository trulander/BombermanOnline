from typing import TypedDict


class Inputs(TypedDict):
    up: bool
    down: bool
    left: bool
    right: bool
    weapon1: bool  # Основное оружие
    action1: bool  # дополнительное действие для оружия 1
    weapon2: bool  # Вторичное оружие
