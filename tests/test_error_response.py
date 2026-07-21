"""Test the shared _error_response helper."""
from oscmcp.tools import _error_response


def test_error_response_basic():
    result = _error_response("something broke", "general")
    assert result["success"] is False
    assert result["error"] == "something broke"
    assert result["error_type"] == "general"


def test_error_response_with_extra():
    result = _error_response("not found", "not_found", status_code=404)
    assert result["success"] is False
    assert result["status_code"] == 404


def test_error_response_different_types():
    result = _error_response("auth failed", "auth")
    assert result["error_type"] == "auth"
