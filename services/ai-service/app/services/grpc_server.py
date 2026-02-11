import logging
import numpy as np
from concurrent import futures

import grpc

from ..config import settings
from ..inference.inference_service import InferenceService
from ..training.trainer import TrainingService


logger = logging.getLogger(__name__)


try:
    from ..shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger.critical(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )
    raise Exception(e)


class AIServiceServicer:
    def __init__(
        self,
        training_service: TrainingService | None,
        inference_service: InferenceService | None,
    ) -> None:
        self.training_service = training_service
        self.inference_service = inference_service

    def StartTraining(
        self,
        request: bomberman_ai_pb2.TrainingStartRequest,
        context: grpc.ServicerContext,
    ) -> bomberman_ai_pb2.TrainingStartResponse:
        if self.training_service is None:
            return bomberman_ai_pb2.TrainingStartResponse()
        self.training_service.start_training(
            total_timesteps=1000,
            log_name="bomberman_ai",
        )
        return bomberman_ai_pb2.TrainingStartResponse()

    def InferAction(
        self,
        request: bomberman_ai_pb2.InferActionRequest,
        context: grpc.ServicerContext,
    ) -> bomberman_ai_pb2.InferActionResponse:
        if self.inference_service is None:
            return bomberman_ai_pb2.InferActionResponse(action=0)
        if self.inference_service.model is None:
            self.inference_service.load_model()
        if request.observation is None:
            return bomberman_ai_pb2.InferActionResponse(action=0)
        observation = np.array(request.observation.values, dtype=np.float32)
        if observation.size == 0:
            return bomberman_ai_pb2.InferActionResponse(action=0)
        try:
            action = self.inference_service.infer_action(observation=observation)
        except Exception:
            action = 0
        return bomberman_ai_pb2.InferActionResponse(action=int(action))


def start_grpc(
    training_service: TrainingService | None = None,
    inference_service: InferenceService | None = None,
) -> grpc.Server:
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=5))
    bomberman_ai_pb2_grpc.add_AIServiceServicer_to_server(
        AIServiceServicer(
            training_service=training_service,
            inference_service=inference_service,
        ),
        server,
    )
    listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info(f"AI gRPC server started on {listen_addr}")

    return server


def stop_grpc(server: grpc.Server | None):
    if not server:
        logger.warning("no server to stop")
        return

    logger.info("Stopping gRPC server...")
    server.stop(grace=5)
