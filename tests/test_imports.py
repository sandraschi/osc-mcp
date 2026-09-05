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
    from oscmcp.apps import OBSOSC, QLabOSC, VRChatOSC

    assert OBSOSC is not None
    assert QLabOSC is not None
    assert VRChatOSC is not None
