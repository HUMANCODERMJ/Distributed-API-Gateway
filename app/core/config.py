"""
Application configuration module.
Centralized configuration for routes, Redis, logging, and other settings.
"""

import os
from typing import Dict, Optional

# Application settings
APP_NAME = "Distributed API Gateway"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Route configuration - maps request paths to downstream service URLs
# Format: "/prefix" -> "http://downstream-service:port"
ROUTES: Dict[str, str] = {
    "/users": "http://localhost:8001",
    "/orders": "http://localhost:8002",
    "/ai": "http://localhost:8003",
}

# HTTP client configuration
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30.0"))
HTTP_POOL_SIZE = int(os.getenv("HTTP_POOL_SIZE", "100"))

# Health check endpoint
HEALTH_CHECK_PATH = "/health"
READINESS_CHECK_PATH = "/readiness"
