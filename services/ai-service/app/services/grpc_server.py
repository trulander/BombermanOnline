import logging
import numpy as np
from concurrent import futures

import grpc

from app.services.inference_service import InferenceService
from app.services.trainer_service import TrainingService
from ..config import settings
from ..shared.proto.bomberman_ai_pb2 import Observation

logger = logging.getLogger(__name__)


try:
    from ..shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger.critical(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )
    raise Exception(e)


def _parse_observation_from_request(
    observation: Observation,
) -> dict[str, np.ndarray] | None:
    if observation is None:
        return None
    grid_flat: np.ndarray = np.array(observation.grid_values, dtype=np.float32)
    stats: np.ndarray = np.array(observation.stats_values, dtype=np.float32)
    expected_grid: int = settings.GRID_CHANNELS * settings.WINDOW_SIZE * settings.WINDOW_SIZE
    if grid_flat.size != expected_grid or stats.size != settings.STATS_SIZE:
        return None
    grid: np.ndarray = grid_flat.reshape(settings.GRID_CHANNELS, settings.WINDOW_SIZE, settings.WINDOW_SIZE)
    return {"grid": grid, "stats": stats}


class AIServiceServicer:
    server: grpc.Server | None = None

    def __init__(
        self,
        training_service: TrainingService | None,
        inference_service: InferenceService | None,
    ) -> None:
        self.training_service = training_service
        self.inference_service = inference_service
        self.inference_service.load_model()

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

        obs: dict[str, np.ndarray] | None = _parse_observation_from_request(
            observation=request.observation,
        )
        if obs is None:
            logger.warning("InferAction: observation is empty or malformed, returning action=0")
            return bomberman_ai_pb2.InferActionResponse(action=0)

        entity_id: str = request.entity_id or "unknown"
        session_id: str = request.session_id or None
        try:
            action: int = self.inference_service.infer_action(
                observation=obs,
                entity_id=entity_id,
                session_id=session_id
            )
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
