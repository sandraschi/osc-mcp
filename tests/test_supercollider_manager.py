"""Regression test for supercollider_manager's wrong default port.

Verified against a real scsynth.exe (SuperCollider 3.14.1): the binary has
NO built-in default port at all - it refuses to start without an explicit
-u/-t flag ("ERROR: There must be a -u and/or a -t options"). 57110 is the
SuperCollider *language* convention (sclang's `Server.default` binds
NetAddr("127.0.0.1", 57110)), which every tutorial, the official docs, and
this repo's own app_detect.py already assumed - but supercollider_manager's
own `port` parameter defaulted to 57120, a port nothing in the SuperCollider
ecosystem uses by convention.
"""

from unittest.mock import AsyncMock, patch

import pytest

from oscmcp.mcp_server import supercollider_manager


@pytest.mark.asyncio
async def test_default_port_matches_supercollider_language_convention():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await supercollider_manager("create_synth", def_name="default", node_id=1000)

    args = mock_send.await_args.args
    assert args[1] == 57110


@pytest.mark.asyncio
async def test_create_group_sends_real_g_new_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await supercollider_manager("create_group", node_id=100, add_action=1, target=0)

    args = mock_send.await_args.args
    assert args[2] == "/g_new"
    assert args[3] == [100, 1, 0]


@pytest.mark.asyncio
async def test_free_group_sends_real_g_freeall_address():
    with patch("oscmcp.mcp_server.send_osc", new=AsyncMock(return_value={"status": "success"})) as mock_send:
        await supercollider_manager("free_group", node_id=100)

    args = mock_send.await_args.args
    assert args[2] == "/g_freeAll"
    assert args[3] == [100]


@pytest.mark.asyncio
async def test_status_returns_real_telemetry_on_successful_query():
    """`status` is the one genuinely bidirectional operation here - verified live
    against a real running scsynth.exe (3.14.1) before writing this test, not
    just mocked speculatively. See _query_scsynth_status's docstring for the
    real, documented /status.reply argument order this parses.
    """
    fake_reply = {
        "num_ugens": 3,
        "num_synths": 1,
        "num_groups": 2,
        "num_synthdefs": 5,
        "avg_cpu_percent": 0.5,
        "peak_cpu_percent": 0.8,
        "nominal_sample_rate": 48000.0,
        "actual_sample_rate": 47999.9,
    }
    with patch("oscmcp.mcp_server._query_scsynth_status", new=AsyncMock(return_value=fake_reply)):
        result = await supercollider_manager("status")

    assert result["status"] == "success"
    assert result["num_groups"] == 2
    assert result["actual_sample_rate"] == 47999.9


@pytest.mark.asyncio
async def test_status_reports_timeout_clearly():
    with patch("oscmcp.mcp_server._query_scsynth_status", new=AsyncMock(side_effect=TimeoutError())):
        result = await supercollider_manager("status")

    assert result["status"] == "error"
    assert "scsynth" in result["message"]


@pytest.mark.asyncio
async def test_status_reports_connection_reset_clearly():
    """Windows-specific: sending UDP to a port nothing is listening on gets an
    ICMP port-unreachable back as a ConnectionResetError, not a plain timeout -
    confirmed live against an unbound port before writing this test.
    """
    with patch("oscmcp.mcp_server._query_scsynth_status", new=AsyncMock(side_effect=ConnectionResetError())):
        result = await supercollider_manager("status")

    assert result["status"] == "error"
    assert "Nothing is listening" in result["message"]
