import numpy as np

from app.services.grpc_server import AIServiceServicer
from app.shared.proto import bomberman_ai_pb2


class FakeInference:
    def __init__(self) -> None:
        self.model = None
        self.loaded = False

    def load_model(self) -> bool:
        self.loaded = True
        self.model = object()
        return True

    def infer_action(self, observation: np.ndarray) -> int:
        return 4


def test_infer_action_empty_observation_returns_zero() -> None:
    inference_service = FakeInference()
    servicer = AIServiceServicer(training_service=None, inference_service=inference_service)
    request = bomberman_ai_pb2.InferActionRequest(
        session_id="s1",
        entity_id="e1",
        observation=bomberman_ai_pb2.Observation(values=[]),
    )

    response = servicer.InferAction(request=request, context=None)

    assert response.action == 0


def test_infer_action_returns_value() -> None:
    inference_service = FakeInference()
    servicer = AIServiceServicer(training_service=None, inference_service=inference_service)
    request = bomberman_ai_pb2.InferActionRequest(
        session_id="s1",
        entity_id="e1",
        observation=bomberman_ai_pb2.Observation(values=[0.2, 0.3]),
    )

    response = servicer.InferAction(request=request, context=None)

    assert response.action == 4

