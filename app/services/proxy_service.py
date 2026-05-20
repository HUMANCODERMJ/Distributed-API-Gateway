"""
Proxy service module.
Handles forwarding requests to downstream services.
"""

import httpx
from typing import Optional
from fastapi import Request, Response
from urllib.parse import urljoin

from app.core.config import ROUTES, HTTP_TIMEOUT, HTTP_POOL_SIZE
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ProxyService:
    """Handles HTTP request forwarding to downstream services."""
    
    _client: httpx.AsyncClient = None
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """
        Get or create HTTP client.
        
        Returns:
            httpx.AsyncClient instance
        """
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                limits=httpx.Limits(max_connections=HTTP_POOL_SIZE)
            )
            logger.info("HTTP client initialized")
        
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close HTTP client connection."""
        if cls._client:
            await cls._client.aclose()
            cls._client = None
            logger.info("HTTP client closed")
    
    @staticmethod
    def get_downstream_url(request_path: str) -> Optional[str]:
        """
        Match request path to a downstream service URL.
        Routes are matched by prefix.
        
        Args:
            request_path: The incoming request path
        
        Returns:
            Downstream service URL if matched, None otherwise
        """
        # Remove leading/trailing slashes for comparison
        normalized_path = request_path.strip("/")
        
        # Try exact and prefix matches
        for route_prefix, service_url in ROUTES.items():
            prefix = route_prefix.strip("/")
            
            # Check if path starts with this route prefix
            if normalized_path.startswith(prefix) or normalized_path == prefix:
                return service_url
        
        return None
    
    @staticmethod
    async def forward_request(
        request: Request,
        downstream_url: str,
        full_path: str
    ) -> Response:
        """
        Forward an incoming request to a downstream service and return the response.
        
        Args:
            request: The incoming FastAPI request
            downstream_url: Base URL of the downstream service
            full_path: The full request path
        
        Returns:
            FastAPI Response with downstream status and content
        """
        client = await ProxyService.get_client()
        
        # Construct the full downstream URL
        target_url = urljoin(downstream_url, "/" + full_path.lstrip("/"))
        
        # Get request method
        method = request.method
        
        # Forward headers (exclude some connection-related headers)
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("connection", None)
        
        # Get query parameters
        query_params = dict(request.query_params) if request.query_params else {}
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        try:
            logger.info("Forwarding %s %s to %s", method, full_path, target_url)
            
            # Forward the request
            downstream_response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=query_params,
                content=body,
                follow_redirects=True
            )
            
            logger.info(
                "Downstream response: %s from %s",
                downstream_response.status_code,
                target_url,
            )
            
            # Return downstream response as-is
            return Response(
                content=downstream_response.content,
                status_code=downstream_response.status_code,
                headers=dict(downstream_response.headers),
                media_type=downstream_response.headers.get("content-type")
            )
        
        except httpx.RequestError as e:
            logger.error("Request forwarding error: %s", e)
            return Response(
                content={"error": f"Downstream service error: {str(e)}"},
                status_code=502,
                media_type="application/json"
            )
