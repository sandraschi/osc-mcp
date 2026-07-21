"""Shared tool utilities and helpers."""

import logging

logger = logging.getLogger(__name__)


def _error_response(error: str, error_type: str = "general", **kwargs) -> dict:
    """Build a standard error response dict with auto-logging.

    Call from inside ``except`` blocks so ``logger.exception`` captures
    the active traceback automatically.

    Args:
        error: Human-readable error message.
        error_type: Short category (validation, auth, not_found, …).
        **kwargs: Extra keys merged into the response dict.

    Returns:
        Dict with ``success=False``, ``error``, ``error_type``, plus any
        extra kwargs.
    """
    logger.exception("Tool error: %s [%s]", error, error_type)
    return {"success": False, "error": error, "error_type": error_type, **kwargs}


__all__ = ["_error_response"]
