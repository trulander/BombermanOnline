from concurrent import futures

import grpc
import numpy as np

from app.services.grpc_server import AIServiceServicer
from app.shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc


class FakeInference:
    def __init__(self) -> None:
        self.model = object()

    def load_model(self) -> bool:
        return True

    def infer_action(self, observation: np.ndarray) -> int:
        return 7


def test_grpc_infer_action_roundtrip() -> None:
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=1))
    servicer = AIServiceServicer(training_service=None, inference_service=FakeInference())
    bomberman_ai_pb2_grpc.add_AIServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("localhost:0")
    server.start()

    channel = grpc.insecure_channel(target=f"localhost:{port}")
    stub = bomberman_ai_pb2_grpc.AIServiceStub(channel)
    request = bomberman_ai_pb2.InferActionRequest(
        session_id="s1",
        entity_id="e1",
        observation=bomberman_ai_pb2.Observation(values=[0.1, 0.2]),
    )

    response = stub.InferAction(request)

    server.stop(grace=0)
    channel.close()
    assert response.action == 7

