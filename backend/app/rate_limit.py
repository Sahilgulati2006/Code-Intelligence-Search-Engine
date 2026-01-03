# app/rate_limit.py
"""Rate limiting utilities."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from functools import wraps
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Initialize rate limiter
# Uses IP address by default, falls back to "default" if IP can't be determined
limiter = Limiter(key_func=get_remote_address)


def rate_limit_key(request: Request) -> str:
    """
    Custom key function for rate limiting.
    
    Uses IP address, with fallback to "default" if not available.
    """
    remote_address = get_remote_address(request)
    return remote_address or "default"


def get_rate_limit_string() -> str:
    """Get rate limit string for slowapi."""
    if not settings.RATE_LIMIT_ENABLED:
        return None

    # Format: "100/minute"
    requests = settings.RATE_LIMIT_REQUESTS
    window = settings.RATE_LIMIT_WINDOW

    if window == 60:
        return f"{requests}/minute"
    elif window == 3600:
        return f"{requests}/hour"
    else:
        return f"{requests}/{window}s"


class RateLimitManager:
    """Manage rate limiting for specific endpoints."""

    @staticmethod
    def is_enabled() -> bool:
        """Check if rate limiting is enabled."""
        return settings.RATE_LIMIT_ENABLED

    @staticmethod
    def get_limiter():
        """Get the limiter instance."""
        if not RateLimitManager.is_enabled():
            return None
        return limiter

    @staticmethod
    def create_limit_decorator():
        """
        Create a rate limit decorator dynamically.

        Returns:
            Decorator function or a no-op decorator if disabled
        """
        if not RateLimitManager.is_enabled():
            # Return a no-op decorator
            def noop_decorator(func):
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    return await func(*args, **kwargs) if hasattr(func(None), '__await__') else func(*args, **kwargs)
                return wrapper
            return noop_decorator

        rate_limit_str = get_rate_limit_string()
        return limiter.limit(rate_limit_str)


def handle_rate_limit_error(request: Request, exc: RateLimitExceeded):
    """Custom error handler for rate limit exceeded."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many requests. {exc.detail}",
    )


# Predefined rate limit decorators for different endpoints
class EndpointLimits:
    """Rate limits for different endpoint categories."""

    @staticmethod
    def search_limit():
        """Rate limit for search endpoints (more permissive)."""
        if not settings.RATE_LIMIT_ENABLED:
            return limiter.limit("unlimited")  # No limit
        return limiter.limit(f"{settings.RATE_LIMIT_REQUESTS * 2}/minute")  # 2x normal

    @staticmethod
    def index_limit():
        """Rate limit for indexing endpoints (stricter)."""
        if not settings.RATE_LIMIT_ENABLED:
            return limiter.limit("unlimited")  # No limit
        return limiter.limit(f"{settings.RATE_LIMIT_REQUESTS // 2}/minute")  # 0.5x normal

    @staticmethod
    def general_limit():
        """Rate limit for general endpoints."""
        if not settings.RATE_LIMIT_ENABLED:
            return limiter.limit("unlimited")  # No limit
        rate_limit_str = get_rate_limit_string()
        return limiter.limit(rate_limit_str)


# Example usage in endpoints:
# from slowapi import Limiter
# from app.rate_limit import EndpointLimits
#
# @app.post("/search")
# @EndpointLimits.search_limit()
# async def search(request: Request, body: SearchRequest):
#     ...
