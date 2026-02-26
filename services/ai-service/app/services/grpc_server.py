import logging
import numpy as np
from concurrent import futures

import grpc

from app.services.inference_service import InferenceService
from app.services.trainer_player_service import STATS_PLAYER_INFERENCE_SIZE, GRID_PLAYER_INFERENCE_CHANNELS
from .trainer_enemy_service import GRID_ENEMY_INFERENCE_CHANNELS, STATS_ENEMY_INFERENCE_SIZE
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


def _parse_observation(observation: Observation, shape: tuple[int, ...], stats_size: int) -> dict[str, np.ndarray]:
    grid_flat: np.ndarray = np.array(observation.grid_values, dtype=np.float32)
    stats: np.ndarray = np.array(observation.stats_values, dtype=np.float32)

    expected_grid: int = shape[0] * shape[1] * shape[2]
    if grid_flat.size == expected_grid:
        grid: np.ndarray = grid_flat.reshape(shape[0], shape[1], shape[2])
    else:
        grid = np.zeros((shape[0], shape[1], shape[2]), dtype=np.float32)

    if stats.size != stats_size:
        stats = np.zeros(stats_size, dtype=np.float32)

    return {"grid": grid, "stats": stats}


class AIServiceServicer:
    server: grpc.Server | None = None

    def __init__(
        self,
        inference_service: InferenceService | None,
    ) -> None:
        self.inference_service = inference_service
        self.model_name_player_inference: str = "10000000"
        self.model_name_enemy_inference: str = "enemy1000000"

        self.inference_service.load_model(
            model_name=self.model_name_player_inference
        )
        self.inference_service.load_model(
            model_name=self.model_name_enemy_inference
        )

    def InferPlayerAction(
        self,
        request: bomberman_ai_pb2.InferActionRequest,
        context: grpc.ServicerContext,
    ) -> bomberman_ai_pb2.InferActionResponse:
        return self._infer_action(
            request=request,
            model_name=self.model_name_player_inference,
            shape=(GRID_PLAYER_INFERENCE_CHANNELS, settings.WINDOW_SIZE, settings.WINDOW_SIZE),
            stats_size=STATS_PLAYER_INFERENCE_SIZE
        )

    def InferEnemyAction(
        self,
        request: bomberman_ai_pb2.InferActionRequest,
        context: grpc.ServicerContext,
    ) -> bomberman_ai_pb2.InferActionResponse:
        return self._infer_action(
            request=request,
            model_name=self.model_name_enemy_inference,
            shape=(GRID_ENEMY_INFERENCE_CHANNELS, settings.WINDOW_SIZE, settings.WINDOW_SIZE),
            stats_size=STATS_ENEMY_INFERENCE_SIZE
        )

    def _infer_action(
            self,
            request: bomberman_ai_pb2.InferActionRequest,
            model_name: str,
            shape: tuple[int, ...],
            stats_size: int,
    ) -> bomberman_ai_pb2.InferActionResponse:
        logger.debug("gRPC InferAction called")
        if self.inference_service is None:
            logger.warning("InferAction: inference_service is None, returning action=0")
            return bomberman_ai_pb2.InferActionResponse(action=0)

        # if self.inference_service.model is None:
        #     logger.info("InferAction: model not loaded, loading model")

        obs: dict[str, np.ndarray] | None = _parse_observation(
            observation=request.observation,
            stats_size=stats_size,
            shape=shape
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
                session_id=session_id,
                model_name=model_name
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
