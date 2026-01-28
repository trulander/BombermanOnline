import logging
from concurrent import futures

import grpc

try:
    from ..shared.proto import bomberman_ai_pb2, bomberman_ai_pb2_grpc
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("Proto files not generated yet. Run generate.sh in services/shared/proto/")
    raise Exception(e)

from ..config import settings


logger = logging.getLogger(__name__)


class AIServiceServicer():
    def __init__(self, ):
        pass




def start_grpc():
    server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=5))
    # bomberman_ai_pb2_grpc.add_AIServiceServicer_to_server(AIServiceServicer(), server)
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
