"""Tests for vrchat_manager, including the operations ported from the
stranded goofy-bardeen branch (movement/camera/action input, chatbox typing
indicator, tracker control, AFK toggle) - never merged into master, and
absent from the live tool until this port.

Addresses match VRChat's official OSC spec (docs.vrchat.com/docs/osc-overview)
- not live-verified against a running VRChat session in this pass (unlike the
resolume_manager fix, which was), since that requires a loaded avatar/world.
"""

from unittest.mock import AsyncMock, patch

import pytest

from oscmcp.mcp_server import vrchat_manager


@pytest.mark.asyncio
async def test_input_sends_to_input_namespace():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("input", input_name="MoveForward", value=1.0)

    args = mock_send.await_args.args
    assert args[2] == "/input/MoveForward"
    assert args[3] == [1.0]


@pytest.mark.asyncio
async def test_input_requires_input_name_and_value():
    result = await vrchat_manager("input", input_name=None, value=None)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_chatbox_typing_sends_typing_indicator():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("chatbox_typing", message="thinking...")

    args = mock_send.await_args.args
    assert args[2] == "/chatbox/typing"
    assert args[3] == ["thinking..."]


@pytest.mark.asyncio
async def test_send_chat_notify_defaults_false_but_is_controllable():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("send_chat", message="hi")
    assert mock_send.await_args.args[3] == ["hi", True, False]

    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("send_chat", message="hi", notify=True)
    assert mock_send.await_args.args[3] == ["hi", True, True]


@pytest.mark.asyncio
async def test_tracking_control_sends_to_tracking_namespace():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("tracking_control", tracking_type="LeftFoot", enabled=False)

    args = mock_send.await_args.args
    assert args[2] == "/tracking/LeftFoot/enabled"
    assert args[3] == [0]


@pytest.mark.asyncio
async def test_afk_toggle_sets_the_afk_avatar_parameter():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("afk_toggle", enabled=True)

    args = mock_send.await_args.args
    assert args[2] == "/avatar/parameters/AFK"
    assert args[3] == [1]
