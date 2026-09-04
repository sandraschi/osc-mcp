"""Regression coverage for the tool-wiring and Prefab DataTable bugs found in the
2026-09-04 quality-check (see reports/quality-osc-mcp-2026-09-04.md).

Two independent bugs shipped silently because nothing exercised these paths:
1. The 11 app-manager tools (Ableton, VCV Rack, TouchDesigner, ...) were defined in
   mcp_server.py but never imported by server.py, so they never reached
   ``server.list_tools()`` and were unreachable by any MCP client.
2. Five Prefab dashboard tools called ``DataTableColumn(name=, label=)`` /
   ``DataTable(data=)`` against a prefab_ui version whose real fields are
   ``key``/``header``/``rows`` -- every call raised a pydantic ValidationError.
"""

import pytest

from oscmcp.server import server

EXPECTED_MANAGER_TOOLS = {
    "ableton_manager",
    "vcv_manager",
    "touchdesigner_manager",
    "vrchat_manager",
    "supercollider_manager",
    "maxmsp_manager",
    "resolume_manager",
    "puredata_manager",
    "audio_workflow_manager",
    "osc_recorder_manager",
    "music_orchestrator",
}

PREFAB_TABLE_TOOLS = [
    ("show_active_mappings", {}),
    ("show_discovered_devices", {}),
    ("show_available_workflows", {}),
    ("show_control_faders", {}),
    ("show_osc_oscilloscope", {}),
    ("show_recent_messages", {"port": 9000}),
]


async def test_app_manager_tools_are_registered():
    """The mcp_server.py app managers must be mounted on the live server."""
    tools = await server.list_tools()
    names = {t.name for t in tools}
    missing = EXPECTED_MANAGER_TOOLS - names
    assert not missing, f"App-manager tools not registered on live server: {missing}"


@pytest.mark.parametrize("name,args", PREFAB_TABLE_TOOLS)
async def test_prefab_table_tools_do_not_crash(name, args):
    """DataTable/DataTableColumn Prefab cards must not raise on call."""
    result = await server.call_tool(name, args)
    assert result is not None
