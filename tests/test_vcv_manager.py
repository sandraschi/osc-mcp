"""Regression tests for vcv_manager, corrected 2026-09-05 against the real,
primary-source OSCelot manual (github.com/The-Modular-Mind/oscelot).

Previously this tool sent `/param [module_id, param_id, value]`, `/cv`,
`/light`, `/midi/*`, and `/transport/*` addresses - none of which exist in
OSCelot's actual, documented OSC protocol (verified by fetching the real
manual, not by installing the plugin - it requires a paid VCV Library
account this session shouldn't create on the user's behalf). The manual
documents exactly three message types (`/fader`, `/encoder`, `/button`),
each addressed by a mapping-slot Id assigned by hand in OSCelot's UI - no
direct module/param addressing exists at all.
"""

from unittest.mock import AsyncMock, patch

import pytest

from oscmcp.mcp_server import vcv_manager


@pytest.mark.asyncio
async def test_set_parameter_uses_the_real_fader_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vcv_manager("set_parameter", module_id=1, value=0.5)

    args = mock_send.await_args.args
    assert args[2] == "/fader"
    assert args[3] == [1, 0.5]


@pytest.mark.asyncio
async def test_trigger_uses_the_real_button_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vcv_manager("trigger", module_id=0)

    args = mock_send.await_args.args
    assert args[2] == "/button"
    assert args[3] == [0, 1.0]


@pytest.mark.asyncio
async def test_sync_reaper_tempo_normalizes_and_uses_fader():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await vcv_manager("sync_reaper_tempo", module_id=2, reaper_tempo=120.0)

    args = mock_send.await_args.args
    assert args[2] == "/fader"
    assert args[3] == [2, 1.0]


@pytest.mark.parametrize(
    "operation",
    [
        "send_cv",
        "set_light",
        "play_midi",
        "stop_midi",
        "send_midi_cc",
        "start_transport",
        "stop_transport",
        "reset_transport",
        "set_transport_position",
    ],
)
@pytest.mark.asyncio
async def test_operations_with_no_verified_real_address_are_honestly_rejected(operation):
    """These used to silently fire an unverified guessed address into the
    void. Now they return a clear error instead of pretending to work."""
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock()) as mock_send:
        result = await vcv_manager(operation)

    mock_send.assert_not_awaited()
    assert result["status"] == "error"
    assert result.get("error_code") == "UNSUPPORTED_OPERATION"
