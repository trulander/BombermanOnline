import logging
from typing import Optional, Tuple

import grpc
import numpy as np

import app.main
from .game_service_finder import GameServiceFinder

try:
    from app.shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("Proto files not generated yet. Run generate.sh in services/shared/proto/")
    raise Exception(e)


logger = logging.getLogger(__name__)


class GameServiceGRPCClient:
    def __init__(self, game_service_finder=None):
        self.channel: Optional[grpc.Channel] = None
        # self.stub: Optional[bomberman_ai_pb2_grpc.GameServiceStub] = None
        self.game_service_finder = game_service_finder
        self.current_instance: Optional[dict] = None

    def connect(self):
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
            self.channel = grpc.aio.insecure_channel(address)
            # self.stub = bomberman_ai_pb2_grpc.GameServiceStub(self.channel)
            logger.info(f"Connected to game-service gRPC at {address}")

    def disconnect(self):
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
            logger.info("Disconnected from game-service gRPC")

    def step(
        self,
    ) -> Tuple[np.ndarray, float, bool, bool, dict]:
        pass

    def reset(
        self,
    ) -> Tuple[np.ndarray, dict, str]:
        pass

