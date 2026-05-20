"""
Proxy routes module.
Catch-all endpoint for routing requests to downstream services.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.services.proxy_service import ProxyService
from app.services.redis_service import RedisService
from app.core.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_route(request: Request, full_path: str):
    """
    Catch-all proxy endpoint that forwards requests to downstream services.
    
    Args:
        request: The incoming request
        full_path: The full request path (captured by path parameter)
    
    Returns:
        Response from downstream service or error response
    """
    # Check rate limit
    try:
        client_id = request.client.host if request.client else "unknown"
        rate_limit_key = f"gateway:ratelimit:{client_id}"
        
        count, allowed = await RedisService.check_rate_limit(
            key=rate_limit_key,
            limit=RATE_LIMIT_REQUESTS,
            window=RATE_LIMIT_WINDOW
        )
        
        if not allowed:
            logger.warning("Rate limit exceeded for %s: %s requests", client_id, count)
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
    except RedisError as e:
        logger.warning("Rate limiting check failed: %s, continuing without limit", e)
    
    # Find downstream service
    downstream_url = ProxyService.get_downstream_url(request.url.path)
    
    if not downstream_url:
        logger.warning("No route found for path: %s", request.url.path)
        return JSONResponse(
            status_code=404,
            content={"error": f"No route configured for path: {request.url.path}"}
        )
    
    # Forward request to downstream service
    response = await ProxyService.forward_request(
        request=request,
        downstream_url=downstream_url,
        full_path=full_path
    )
    
    return response
