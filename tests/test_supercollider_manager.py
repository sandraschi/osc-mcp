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
