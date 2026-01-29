import logging
from concurrent import futures

import grpc

try:
    from ..shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
    PROTO_AVAILABLE = True
except ImportError:
    bomberman_ai_pb2 = None
    bomberman_ai_pb2_grpc = None
    PROTO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )

from ..config import settings
from ..inference.inference_service import InferenceService
from ..training.trainer import TrainingService


logger = logging.getLogger(__name__)


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
        request: object,
        context: grpc.ServicerContext,
    ) -> object | None:
        if self.training_service is None:
            return None
        self.training_service.start_training(
            total_timesteps=1000,
            log_name="bomberman_ai",
        )
        return None

    def InferAction(
        self,
        request: object,
        context: grpc.ServicerContext,
    ) -> object | None:
        if self.inference_service is None:
            return None
        return None




def start_grpc(
    training_service: TrainingService | None = None,
    inference_service: InferenceService | None = None,
) -> grpc.Server:
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=5))
    if PROTO_AVAILABLE and bomberman_ai_pb2_grpc is not None:
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
