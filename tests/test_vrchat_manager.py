"""Tests for vrchat_manager, including the operations ported from the
stranded goofy-bardeen branch (movement/camera/action input, chatbox typing
indicator, tracker control, AFK toggle) - never merged into master, and
absent from the live tool until this port.

Addresses match VRChat's official OSC spec (docs.vrchat.com/docs/osc-overview)
- not live-verified against a running VRChat session in this pass (unlike the
resolume_manager fix, which was), since that requires a loaded avatar/world.

`chatbox_typing` and `tracking_control` were re-verified during a later pass
of per-app skill research and found wrong even against this same primary
source: `/chatbox/typing` takes a bool, not the message text, and there is
no real `/tracking/{name}/enabled` address at all (VRChat's real tracking
OSC surface only accepts numbered-slot position/rotation input from
external hardware, with no enable/disable toggle by name) - both fixed,
tests below updated to match.
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
async def test_chatbox_typing_sends_a_bool_not_the_message():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("chatbox_typing", enabled=True)

    args = mock_send.await_args.args
    assert args[2] == "/chatbox/typing"
    assert args[3] == [True]

    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("chatbox_typing", enabled=False)
    assert mock_send.await_args.args[3] == [False]


@pytest.mark.asyncio
async def test_send_chat_notify_defaults_false_but_is_controllable():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("send_chat", message="hi")
    assert mock_send.await_args.args[3] == ["hi", True, False]

    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("send_chat", message="hi", notify=True)
    assert mock_send.await_args.args[3] == ["hi", True, True]


@pytest.mark.asyncio
async def test_tracking_control_is_unsupported():
    # No real VRChat OSC address exists to enable/disable a body tracker by
    # name - this operation used to fabricate /tracking/{name}/enabled.
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        result = await vrchat_manager("tracking_control", tracking_type="LeftFoot", enabled=False)

    mock_send.assert_not_awaited()
    assert result["status"] == "error"
    assert result["error_code"] == "UNSUPPORTED_OPERATION"


@pytest.mark.asyncio
async def test_trigger_haptic_is_unsupported():
    # VRChat has no universal haptic OSC address - this operation used to
    # send /avatar/parameters/LeftHaptic and RightHaptic, neither real.
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        result = await vrchat_manager("trigger_haptic", device="both")

    mock_send.assert_not_awaited()
    assert result["status"] == "error"
    assert result["error_code"] == "UNSUPPORTED_OPERATION"


@pytest.mark.asyncio
async def test_afk_toggle_sets_the_afk_avatar_parameter():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vrchat_manager("afk_toggle", enabled=True)

    args = mock_send.await_args.args
    assert args[2] == "/avatar/parameters/AFK"
    assert args[3] == [1]
