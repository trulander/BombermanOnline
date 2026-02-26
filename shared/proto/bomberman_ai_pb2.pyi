from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Observation(_message.Message):
    __slots__ = ("grid_values", "stats_values")
    GRID_VALUES_FIELD_NUMBER: _ClassVar[int]
    STATS_VALUES_FIELD_NUMBER: _ClassVar[int]
    grid_values: _containers.RepeatedScalarFieldContainer[float]
    stats_values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, grid_values: _Optional[_Iterable[float]] = ..., stats_values: _Optional[_Iterable[float]] = ...) -> None: ...

class TrainingResetRequest(_message.Message):
    __slots__ = ("map_width", "map_height", "enemy_count", "bomb_power", "count_bombs", "player_lives", "training_player", "seed")
    MAP_WIDTH_FIELD_NUMBER: _ClassVar[int]
    MAP_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ENEMY_COUNT_FIELD_NUMBER: _ClassVar[int]
    BOMB_POWER_FIELD_NUMBER: _ClassVar[int]
    COUNT_BOMBS_FIELD_NUMBER: _ClassVar[int]
    PLAYER_LIVES_FIELD_NUMBER: _ClassVar[int]
    TRAINING_PLAYER_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    map_width: int
    map_height: int
    enemy_count: int
    bomb_power: int
    count_bombs: int
    player_lives: int
    training_player: bool
    seed: int
    def __init__(self, map_width: _Optional[int] = ..., map_height: _Optional[int] = ..., enemy_count: _Optional[int] = ..., bomb_power: _Optional[int] = ..., count_bombs: _Optional[int] = ..., player_lives: _Optional[int] = ..., training_player: bool = ..., seed: _Optional[int] = ...) -> None: ...

class TrainingResetResponse(_message.Message):
    __slots__ = ("session_id", "observation", "info_json")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    INFO_JSON_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    observation: Observation
    info_json: str
    def __init__(self, session_id: _Optional[str] = ..., observation: _Optional[_Union[Observation, _Mapping]] = ..., info_json: _Optional[str] = ...) -> None: ...

class TrainingStepRequest(_message.Message):
    __slots__ = ("session_id", "action", "delta_seconds")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DELTA_SECONDS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    action: int
    delta_seconds: float
    def __init__(self, session_id: _Optional[str] = ..., action: _Optional[int] = ..., delta_seconds: _Optional[float] = ...) -> None: ...

class TrainingStepResponse(_message.Message):
    __slots__ = ("observation", "reward", "terminated", "truncated", "info_json")
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    REWARD_FIELD_NUMBER: _ClassVar[int]
    TERMINATED_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    INFO_JSON_FIELD_NUMBER: _ClassVar[int]
    observation: Observation
    reward: float
    terminated: bool
    truncated: bool
    info_json: str
    def __init__(self, observation: _Optional[_Union[Observation, _Mapping]] = ..., reward: _Optional[float] = ..., terminated: bool = ..., truncated: bool = ..., info_json: _Optional[str] = ...) -> None: ...

class InferActionRequest(_message.Message):
    __slots__ = ("session_id", "entity_id", "observation")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    OBSERVATION_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    entity_id: str
    observation: Observation
    def __init__(self, session_id: _Optional[str] = ..., entity_id: _Optional[str] = ..., observation: _Optional[_Union[Observation, _Mapping]] = ...) -> None: ...

class InferActionResponse(_message.Message):
    __slots__ = ("action",)
    ACTION_FIELD_NUMBER: _ClassVar[int]
    action: int
    def __init__(self, action: _Optional[int] = ...) -> None: ...
