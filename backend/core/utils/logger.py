import logging
import os
import sys
from typing import Any

from core.utils.errors import ConfigurationError

env = os.getenv("ENVIRONMENT", "development").lower()
level = logging.INFO if env == "production" else logging.DEBUG

# Silence third-party libraries: make the root logger emit only WARNING and above
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Create a logger
logger = logging.getLogger("CustomsAI")
logger.setLevel(level)

# Add a NullHandler once, so importing this module never raises
# "No handler found" warnings if the app configures logging later.
if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
    logger.addHandler(logging.NullHandler())

# Add our pretty stream handler only if none exist yet (prevents duplicates
# when this module is imported multiple times).
if not logger.handlers or all(isinstance(h, logging.NullHandler) for h in logger.handlers):
    try:
        formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s - %(message)s")
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        # Prevent double-printing on the root logger
        logger.propagate = False
    except Exception as e:
        raise ConfigurationError("Failed to initialize logger", details={"error": str(e)}) from e


def log_with_context(
    level: int, msg: str, extra: dict[str, Any] | None = None, exc_info: bool = False
) -> None:
    """Log a message at the given level, optionally with extra context fields."""
    logger.log(level, msg, extra=extra, exc_info=exc_info)


# Export the logger instance and context-aware logging functions
def error(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.ERROR, msg, extra)


def exception(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.ERROR, msg, extra, exc_info=True)


def info(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.INFO, msg, extra)


def warning(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.WARNING, msg, extra)


def debug(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.DEBUG, msg, extra)


def critical(msg: str, extra: dict[str, Any] | None = None) -> None:
    log_with_context(logging.CRITICAL, msg, extra)
