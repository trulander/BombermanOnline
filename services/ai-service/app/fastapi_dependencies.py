from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.repositories.nats_repository import NatsRepository
    from app.repositories.redis_repository import RedisRepository
    from app.services.game_service_finder import GameServiceFinder
    from app.services.grpc_client import GameServiceGRPCClient
    from app.services.grpc_server import AIServiceServicer
    from app.services.inference_service import InferenceService
    from app.services.trainer_service import TrainingService


def get_redis_repository(request: Request) -> "RedisRepository":
    return request.app.state.redis_repository

def get_nats_repository(request: Request) -> "NatsRepository":
    return request.app.state.nats_repository

def get_game_service_finder(request: Request) -> "GameServiceFinder":
    return request.app.state.game_service_finder

def get_game_service_grpc_client(request: Request) -> "GameServiceGRPCClient":
    return request.app.state.grpc_client

def get_training_service(request: Request) -> "TrainingService":
    return request.app.state.training_service

def get_inference_service(request: Request) -> "InferenceService":
    return request.app.state.inference_service

def get_ai_service(request: Request) -> "AIServiceServicer":
    return request.app.state.ai_service