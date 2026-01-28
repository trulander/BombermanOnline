import asyncio
import logging
from concurrent import futures

import grpc

try:
    from .shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("Proto files not generated yet. Run generate.sh in services/shared/proto/")
    raise Exception(e)

from .config import settings


logger = logging.getLogger(__name__)


class GameServiceServicer():
    def __init__(self):
        pass

    async def Step(self):
        pass

    async def Reset(self):
        pass


async def start_grpc():
    server = grpc.aio.server(migration_thread_pool=futures.ThreadPoolExecutor(max_workers=5))

    # bomberman_ai_pb2_grpc.add_GameServiceServicer_to_server(
    #     GameServiceServicer(), server
    # )

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
    asyncio.run(start_grpc())

