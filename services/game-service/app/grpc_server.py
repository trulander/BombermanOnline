import asyncio
import logging
from concurrent import futures

import grpc

from .config import settings
from .coordinators.training_coordinator import TrainingCoordinator


logger = logging.getLogger(__name__)


try:
    from .shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger.critical(
        msg="Proto files not generated yet. Run generate.sh in services/shared/proto/",
    )
    raise Exception(e)



class GameServiceServicer:
    def __init__(self, training_coordinator: TrainingCoordinator | None) -> None:
        self.training_coordinator = training_coordinator

    async def Step(
        self,
        request: bomberman_ai_pb2.TrainingStepRequest,
        context: grpc.aio.ServicerContext,
    ) -> bomberman_ai_pb2.TrainingStepResponse:
        if self.training_coordinator is None:
            return bomberman_ai_pb2.TrainingStepResponse(
                observation=bomberman_ai_pb2.Observation(grid_values=[], stats_values=[]),
                reward=0.0,
                terminated=True,
                truncated=False,
                info_json="",
            )
        delta_seconds = request.delta_seconds or settings.AI_ACTION_INTERVAL
        result = await self.training_coordinator.step(
            session_id=request.session_id,
            action=request.action,
            delta_seconds=delta_seconds,
        )
        return bomberman_ai_pb2.TrainingStepResponse(
            observation=bomberman_ai_pb2.Observation(
                grid_values=result.grid_values,
                stats_values=result.stats_values,
            ),
            reward=result.reward,
            terminated=result.terminated,
            truncated=result.truncated,
            info_json=result.info_json,
        )

    async def Reset(
        self,
        request: bomberman_ai_pb2.TrainingResetRequest,
        context: grpc.aio.ServicerContext,
    ) -> bomberman_ai_pb2.TrainingResetResponse:
        if self.training_coordinator is None:
            return bomberman_ai_pb2.TrainingResetResponse(
                session_id="",
                observation=bomberman_ai_pb2.Observation(grid_values=[], stats_values=[]),
                info_json="",
            )
        result = await self.training_coordinator.reset(
            map_width=request.map_width or None,
            map_height=request.map_height or None,
            enemy_count=request.enemy_count if request.enemy_count != 0 else None,
            enable_enemies=request.enable_enemies,
            seed=request.seed if request.seed != 0 else None,
        )
        return bomberman_ai_pb2.TrainingResetResponse(
            session_id=result.session_id,
            observation=bomberman_ai_pb2.Observation(
                grid_values=result.grid_values,
                stats_values=result.stats_values,
            ),
            info_json=result.info_json,
        )


async def start_grpc(training_coordinator: TrainingCoordinator | None = None):
    server = grpc.aio.server(migration_thread_pool=futures.ThreadPoolExecutor(max_workers=5))

    bomberman_ai_pb2_grpc.add_GameServiceServicer_to_server(
        GameServiceServicer(training_coordinator=training_coordinator),
        server,
    )

    listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    await server.start()

    logger.info(f"gRPC server started on {listen_addr}")

    return server

async def stop_grpc(server: grpc.aio.Server | None):
    if not server:
        logger.warning("no server to stop")
        return

    logger.info("Stopping gRPC server...")
    await server.stop(grace=5)

def run_grpc_server():
    asyncio.run(start_grpc(training_coordinator=None))

