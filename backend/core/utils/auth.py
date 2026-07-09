"""API-key authentication.

Auth is opt-in: it's enforced only when ``ADMIN_API_KEY`` is configured. With no
key set (e.g. local development or a public demo), all requests pass. Clients
authenticate by sending the key in the ``X-API-Key`` header.
"""

import secrets
from typing import Optional

from fastapi import Security
from fastapi.security import APIKeyHeader

from config import config
from core.utils.errors import AuthenticationError

API_KEY_HEADER_NAME = "X-API-Key"

# auto_error=False so a missing header returns None and we can raise our own
# typed error (mapped to a consistent JSON body by the global handler).
_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


async def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    """Reject the request unless it carries a valid API key.

    No-op when ADMIN_API_KEY is unset. Uses a constant-time comparison so a
    wrong key can't be recovered by timing the response.
    """
    expected = config.app.ADMIN_API_KEY
    if not expected:
        return
    if not api_key or not secrets.compare_digest(api_key, expected):
        raise AuthenticationError("Invalid or missing API key")
