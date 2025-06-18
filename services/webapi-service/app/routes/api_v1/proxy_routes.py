import logging

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.params import Depends
from fastapi.responses import Response

from ...dependencies import game_cache
from ...services.game_cache import GameInstanceCache

logger = logging.getLogger(__name__)


proxy_router = APIRouter()

# @proxy_router.api_route(
#     "/{path:path}",
#     # methods=["GET"]
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]
# )
async def proxy_to_game_service(
        game_id: str,
        path: str,
        request: Request
) -> Response:
    """
    Proxies requests to the game-service.
    """
    game_service_address = await game_cache.get_instance(game_id=game_id)
    if not game_service_address:
        logger.error(f"Game service address not found: {game_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )
    url = httpx.URL(f"http://{game_service_address}:5002/{path}")

    logger.info(f"proxy_to_game_service - url {url}, method: {request.method}")

    # Prepare headers, excluding host which is automatically handled by httpx
    # and any other headers that might cause issues with proxying.
    headers = {key: value for key, value in request.headers.items() if key.lower() not in ["host", "accept-encoding"]}

    # Read the request body
    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            proxy_response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=body,
                timeout=30.0, # You might want to configure this timeout
            )
            proxy_response.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(f"Proxy request to game-service failed: {exc.request.url!r}.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Proxy request to game-service failed: {exc.request.url!r}.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(f"Game-service returned an error: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Game-service returned an error: {exc.response.status_code} - {exc.response.text}",
            ) from exc
    result = Response(
        content=proxy_response.content,
        status_code=proxy_response.status_code,
        headers=proxy_response.headers,
        media_type=proxy_response.headers.get("content-type")
    )
    logger.debug(f"response: {result}")
    return result

for method in ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"]:
    proxy_router.add_api_route(
        "/{path:path}",
        proxy_to_game_service,
        methods=[method],
        name=f"proxy_{method.lower()}"
    )