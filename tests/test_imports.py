"""Test that all modules import without error."""


def test_server_import():
    from oscmcp.server import server
    assert server is not None


def test_api_import():
    from oscmcp.api.main import app
    assert app is not None


def test_tools_import():
    from oscmcp.tools import _error_response
    assert _error_response is not None


def test_apps_import():
    from oscmcp.apps import AbletonLive, VCVController, TouchDesignerOSC
    assert AbletonLive is not None
    assert VCVController is not None
    assert TouchDesignerOSC is not None
