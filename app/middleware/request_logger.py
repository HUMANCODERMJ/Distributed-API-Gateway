"""
Request logging middleware.
Logs incoming requests and outgoing responses.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request, forward to next middleware/route, log response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
        
        Returns:
            Response from downstream
        """
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f">>> {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"<<< {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )
        
        return response
