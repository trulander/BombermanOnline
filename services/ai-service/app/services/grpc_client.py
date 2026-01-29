import logging

import grpc
import numpy as np

import app.main
from .game_service_finder import GameServiceFinder

try:
    from app.shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
    PROTO_AVAILABLE = True
except ImportError:
    bomberman_ai_pb2 = None
    bomberman_ai_pb2_grpc = None
    PROTO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )


logger = logging.getLogger(__name__)


class GameServiceGRPCClient:
    def __init__(
        self,
        game_service_finder: GameServiceFinder | None = None,
    ) -> None:
        self.channel: grpc.aio.Channel | None = None
        self.stub = None
        self.game_service_finder = game_service_finder
        self.current_instance: dict | None = None

    def connect(self) -> None:
        if self.channel is None:
            if not self.current_instance:
                if self.game_service_finder:
                    self.current_instance = self.game_service_finder.find_game_service_instance()
                else:

                    finder = GameServiceFinder(nats_repository=app.main.app.state.nats_repository)
                    self.current_instance = finder.find_game_service_instance()

                if not self.current_instance:
                    raise ConnectionError("No game-service instances available")

            address = f"{self.current_instance['address']}:{self.current_instance['port']}"
            self.channel = grpc.aio.insecure_channel(target=address)
            if PROTO_AVAILABLE and bomberman_ai_pb2_grpc is not None:
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
    ) -> tuple[np.ndarray | None, float, bool, bool, dict]:
        if not PROTO_AVAILABLE or self.stub is None:
            return None, 0.0, False, False, {}
        return None, 0.0, False, False, {}

    def reset(
        self,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray | None, dict, str]:
        if not PROTO_AVAILABLE or self.stub is None:
            return None, {}, "stub-session"
        return None, {}, "stub-session"

