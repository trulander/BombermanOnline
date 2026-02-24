import logging
import json

import grpc
import numpy as np

from .game_service_finder import GameServiceFinder
from ..config import settings
from ..shared.proto.bomberman_ai_pb2 import Observation

logger = logging.getLogger(__name__)


try:
    from app.shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger.critical(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )
    raise Exception(e)



def _parse_observation(observation: Observation) -> dict[str, np.ndarray]:
    grid_flat: np.ndarray = np.array(observation.grid_values, dtype=np.float32)
    stats: np.ndarray = np.array(observation.stats_values, dtype=np.float32)

    expected_grid: int = settings.GRID_CHANNELS * settings.WINDOW_SIZE * settings.WINDOW_SIZE
    if grid_flat.size == expected_grid:
        grid: np.ndarray = grid_flat.reshape(settings.GRID_CHANNELS, settings.WINDOW_SIZE, settings.WINDOW_SIZE)
    else:
        grid = np.zeros((settings.GRID_CHANNELS, settings.WINDOW_SIZE, settings.WINDOW_SIZE), dtype=np.float32)

    if stats.size != settings.STATS_SIZE:
        stats = np.zeros(settings.STATS_SIZE, dtype=np.float32)

    return {"grid": grid, "stats": stats}


class GameServiceGRPCClient:
    def __init__(
        self,
        game_service_finder: GameServiceFinder,
    ) -> None:
        self.channel: grpc.Channel | None = None
        self.stub = None
        self.game_service_finder = game_service_finder
        self.current_instance: dict | None = None
        logger.info("GameServiceGRPCClient initialized")

    def connect(self) -> None:
        if self.channel is None:
            if not self.current_instance:
                self.current_instance = self.game_service_finder.find_game_service_instance()

                if not self.current_instance:
                    raise ConnectionError("No game-service instances available")

            address = f"{self.current_instance['address']}:{self.current_instance['grpc_port']}"
            self.channel = grpc.insecure_channel(target=address)
            self.stub = bomberman_ai_pb2_grpc.GameServiceStub(self.channel)
            logger.info(f"Connected to game-service gRPC at {address}")

    def disconnect(self) -> None:
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
            logger.info("Disconnected from game-service gRPC")

    def step(
        self,
        action: int,
        session_id: str | None,
    ) -> tuple[dict[str, np.ndarray] | None, float, bool, bool, dict]:
        logger.debug(f"gRPC step: action={action}, session_id={session_id}")
        if self.stub is None:
            self.connect()
        if self.stub is None:
            logger.error(f"gRPC step failed: Wasn't able to connect to the game-service grpc server", exc_info=True)
            raise Exception({"error": "Wasn't able to connect to the game-service grpc server"})

        request = bomberman_ai_pb2.TrainingStepRequest(
            session_id=session_id or "",
            action=action,
            delta_seconds=0.33,
        )
        try:
            response = self.stub.Step(request)
        except Exception as exc:
            logger.error(f"gRPC step failed: {exc}", exc_info=True)
            self.disconnect()
            raise

        observation: dict[str, np.ndarray] = _parse_observation(observation=response.observation)
        info = {}
        if response.info_json:
            try:
                info = json.loads(response.info_json)
            except Exception as e:
                logger.warning(f"Failed to parse info_json in step response: {e}")
                raise

        logger.debug(
            f"gRPC step result: reward={response.reward}, "
            f"terminated={response.terminated}, truncated={response.truncated}"
        )
        return observation, float(response.reward), bool(response.terminated), bool(response.truncated), info

    def reset(
        self,
        options: dict[str, object] | None = None,
    ) -> tuple[dict[str, np.ndarray] | None, dict, str]:
        logger.info(f"gRPC reset: options={options}")
        if self.stub is None:
            self.connect()
        if self.stub is None:
            logger.error(f"gRPC reset failed: Wasn't able to connect to the game-service grpc server", exc_info=True)
            raise Exception({"error": "Wasn't able to connect to the game-service grpc server"})

        options = options or {}
        request = bomberman_ai_pb2.TrainingResetRequest(**options)
        try:
            response = self.stub.Reset(request)
        except Exception as exc:
            logger.error(f"gRPC reset failed: {exc}", exc_info=True)
            self.disconnect()
            raise

        observation: dict[str, np.ndarray] = _parse_observation(observation=response.observation)
        info = {}
        if response.info_json:
            try:
                info = json.loads(response.info_json)
            except Exception as e:
                logger.warning(f"Failed to parse info_json in reset response: {e}")
                raise
        logger.info(
            f"gRPC reset result: session_id={response.session_id}"
        )
        return observation, info, response.session_id or "stub-session"
