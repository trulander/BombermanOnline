from app.entities import Inputs


def action_to_inputs(action: int) -> Inputs:
    return Inputs(
        up=(action == 1),
        down=(action == 2),
        left=(action == 3),
        right=(action == 4),
        weapon1=False,
        action1=False,
        weapon2=False,
    )


def action_to_direction(action: int, current: tuple[float, float]) -> tuple[float, float]:
    if action == 1:
        return (0.0, -1.0)
    if action == 2:
        return (0.0, 1.0)
    if action == 3:
        return (-1.0, 0.0)
    if action == 4:
        return (1.0, 0.0)
    return current
