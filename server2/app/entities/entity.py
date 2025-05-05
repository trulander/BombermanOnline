import uuid

class Entity:
    """Базовый класс для всех игровых сущностей."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        entity_id: str | None = None,
        name: str = "",
        ai: bool = False,
        speed: float = 0.0,
        lives: int = 1,
        invulnerable: bool = False,
        invulnerable_timer: float = 0.0,
        color: str = "#FFFFFF"  # Белый цвет по умолчанию
    ):
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.id: str = entity_id if entity_id is not None else str(uuid.uuid4())
        self.name: str = name
        self.ai: bool = ai
        self.speed: float = speed
        self.lives: int = lives
        self.invulnerable: bool = invulnerable
        self.invulnerable_timer: float = invulnerable_timer
        self.color: str = color

    def update(self, delta_time: float) -> None:
        """Обновляет состояние сущности. Должен быть расширен в дочерних классах."""
        # Update invulnerability
        if self.invulnerable:
            self.invulnerable_timer -= delta_time
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                self.invulnerable_timer = 0

    def draw(self) -> dict:
        """Возвращает данные для отрисовки сущности. Может быть переопределен."""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'color': self.color,
            'name': self.name,
            'lives': self.lives,
            'invulnerable': self.invulnerable
        }