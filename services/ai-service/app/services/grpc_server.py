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
    server: grpc.Server | None = None

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
        logger.info("gRPC StartTraining called")
        if self.training_service is None:
            logger.warning("StartTraining: training_service is None, returning empty response")
            return bomberman_ai_pb2.TrainingStartResponse()
        try:
            self.training_service.start_training(
                total_timesteps=1000,
                log_name="bomberman_ai",
            )
            logger.info("StartTraining completed successfully")
        except Exception as e:
            logger.error(f"StartTraining failed: {e}", exc_info=True)
        return bomberman_ai_pb2.TrainingStartResponse()

    def InferAction(
        self,
        request: bomberman_ai_pb2.InferActionRequest,
        context: grpc.ServicerContext,
    ) -> bomberman_ai_pb2.InferActionResponse:
        logger.debug("gRPC InferAction called")
        if self.inference_service is None:
            logger.warning("InferAction: inference_service is None, returning action=0")
            return bomberman_ai_pb2.InferActionResponse(action=0)
        if self.inference_service.model is None:
            logger.info("InferAction: model not loaded, loading model")
            self.inference_service.load_model()
        if request.observation is None:
            logger.warning("InferAction: observation is None, returning action=0")
            return bomberman_ai_pb2.InferActionResponse(action=0)
        observation = np.array(request.observation.values, dtype=np.float32)
        if observation.size == 0:
            logger.warning("InferAction: observation is empty, returning action=0")
            return bomberman_ai_pb2.InferActionResponse(action=0)
        try:
            action = self.inference_service.infer_action(observation=observation)
            logger.debug(f"InferAction: predicted action={action}")
        except Exception as e:
            logger.error(f"InferAction: inference failed: {e}", exc_info=True)
            action = 0
        return bomberman_ai_pb2.InferActionResponse(action=int(action))


    def start_grpc(self) -> grpc.Server:
        if self.server:
            return self.server

        self.server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=5))
        bomberman_ai_pb2_grpc.add_AIServiceServicer_to_server(
            servicer=self,
            server=self.server,
        )
        listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
        self.server.add_insecure_port(listen_addr)
        self.server.start()
        logger.info(f"AI gRPC server started on {listen_addr}")
        return self.server

    def stop_grpc(self):
        if not self.server:
            logger.warning("no server to stop")
            return

        logger.info("Stopping gRPC server...")
        self.server.stop(grace=5)
        self.server = None