"""Regression test for resolume_manager's set_layer_opacity address bug.

Verified live against a real, running Resolume Avenue 7.27.1 instance
(2026-09-05): /composition/layers/{n}/opacity is silently accepted by the
OSC transport but has NO effect in Resolume - the UI opacity slider never
moves. The real address needs a /video/ segment:
/composition/layers/{n}/video/opacity. Confirmed by sending both directly
and watching Resolume's own OSC monitor + the Layer panel's Opacity field.

This module (like all other app-manager modules) had zero test coverage
before this - the exact blind spot that let the wrong address ship
unnoticed.
"""

from unittest.mock import AsyncMock, patch

import pytest

from oscmcp.mcp_server import resolume_manager


@pytest.mark.asyncio
async def test_set_layer_opacity_uses_the_video_opacity_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await resolume_manager("set_layer_opacity", host="127.0.0.1", port=7000, layer=1, opacity=0.5)

    mock_send.assert_awaited_once()
    args = mock_send.await_args.args
    # (host, port, address, values)
    assert args[2] == "/composition/layers/1/video/opacity"
    assert args[3] == [0.5]


@pytest.mark.asyncio
async def test_set_layer_opacity_requires_layer_and_opacity():
    result = await resolume_manager("set_layer_opacity", host="127.0.0.1", port=7000, layer=None, opacity=None)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_play_clip_uses_the_documented_connect_address():
    """Verified live too - this one was already correct."""
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await resolume_manager("play_clip", host="127.0.0.1", port=7000, layer=1, column=2)

    mock_send.assert_awaited_once()
    args = mock_send.await_args.args
    assert args[2] == "/composition/layers/1/clips/2/connect"
