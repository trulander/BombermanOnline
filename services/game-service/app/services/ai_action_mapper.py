from app.entities import Inputs


def action_to_inputs(action: int) -> Inputs:
    return Inputs(
        up=(action == 1),
        down=(action == 2),
        left=(action == 3),
        right=(action == 4),
        weapon1=(action == 5),
        action1=False,
        weapon2=False,
    )

def inputs_to_action(inputs: Inputs) -> int:
    if inputs.up:
        return 1
    if inputs.down:
        return 2
    if inputs.left:
        return 3
    if inputs.right:
        return 4
    if inputs.weapon1:
        return 5

    return 0  # нет действия

def action_to_direction(action: int, current: tuple[int, int] = (0, 0)) -> tuple[int, int]:
    if action == 0:
        return (0, 0)
    if action == 1:
        return (0, -1)
    if action == 2:
        return (0, 1)
    if action == 3:
        return (-1, 0)
    if action == 4:
        return (1, 0)
    return current


def direction_to_action(direction: tuple[int, int]) -> int:
    if direction == (0, 0):
        return 0
    if direction == (0, -1):
        return 1
    if direction == (0, 1):
        return 2
    if direction == (-1, 0):
        return 3
    if direction == (1, 0):
        return 4
    return 0
