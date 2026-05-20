"""
Main gateway application module.
Entry point for the Distributed API Gateway.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.core.config import APP_NAME, APP_VERSION, DEBUG
from app.core.logging_config import get_logger
from app.middleware.request_logger import RequestLoggerMiddleware
from app.routes.proxy import router as proxy_router
from app.services.redis_service import RedisService
from app.services.proxy_service import ProxyService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    logger.info("Debug mode: %s", DEBUG)
    
    try:
        # Initialize Redis connection
        await RedisService.get_client()
        logger.info("Redis connection established")
    except RedisError as e:
        logger.error("Failed to connect to Redis: %s", e)
        logger.warning("Continuing without Redis - rate limiting may not work")
    
    yield
    
    # Shutdown
    logger.info("Shutting down gateway...")
    await RedisService.close()
    await ProxyService.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan
)

# Register middleware
app.add_middleware(RequestLoggerMiddleware)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns 200 if gateway is running.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )


@app.get("/readiness")
async def readiness_check():
    """
    Readiness check endpoint.
    Checks whether the gateway application is running and able to serve traffic.
    """
    try:
        client = await RedisService.get_client()
        try:
            await client.ping()
        except RedisError as redis_error:
            logger.warning("Redis unavailable during readiness check: %s", redis_error)
        
        return JSONResponse(
            status_code=200,
            content={"status": "ready"}
        )
    except RedisError as e:
        logger.warning("Readiness check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )


# Register routes (AFTER specific routes so catch-all doesn't intercept them)
app.include_router(proxy_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info" if not DEBUG else "debug"
    )
