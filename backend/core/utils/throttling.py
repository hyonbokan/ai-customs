import time
from collections import defaultdict, deque
from functools import wraps
from typing import Callable, Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse


def throttle(max_requests: int = 100, window_seconds: int = 60, use_ip: bool = False):
    """
    Simple in-memory sliding-window rate limiter.

    Limits each caller to ``max_requests`` within ``window_seconds``. When
    ``use_ip`` is set, requests are bucketed per client IP (the decorated
    endpoint must declare a ``request: Request`` parameter); otherwise a single
    global bucket is used.

    State is per-process and not shared across workers, which is adequate for
    lightweight protection of a single endpoint. For distributed rate limiting,
    back this with Redis.
    """
    hits: Dict[str, Deque[float]] = defaultdict(deque)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = "global"
            if use_ip:
                request = next((a for a in args if isinstance(a, Request)), kwargs.get("request"))
                if request is not None and request.client:
                    key = request.client.host

            now = time.monotonic()
            bucket = hits[key]
            while bucket and now - bucket[0] > window_seconds:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error_code": "rate_limit_error",
                        "error": "Too many requests",
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
