import os
import redis
from fastapi import Header, Request, HTTPException, status
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Share the connection pool
r = redis.from_url(REDIS_URL)

def is_rate_limited(identifier: str, limit: int = 100, period: int = 60) -> bool:
    """
    Check if a given identifier has exceeded the limit within the period (seconds).
    Returns True if rate limited, False otherwise.
    """
    key = f"rate_limit:{identifier}"
    try:
        current = r.incr(key)
        if current == 1:
            r.expire(key, period)
        if current > limit:
            return True
        return False
    except redis.RedisError as e:
        # Log error but fail open so the service remains available if Redis is down
        print(f"Redis rate limiter exception: {e}")
        return False

async def rate_limiter(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    # Enforce rate limiting: Identify by API Key or fallback to Client IP
    identifier = x_api_key if x_api_key else request.client.host
    
    # Limit: 100 requests per 60 seconds
    if is_rate_limited(identifier, limit=100, period=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per minute."
        )
