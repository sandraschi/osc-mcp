"""OSC-MCP Server Implementation.

This module implements the core OSC server functionality using FastMCP 2.14.3+
and python-osc for Open Sound Control protocol support, with conversational
tool returns and advanced LLM sampling capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import os
import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient

from .sampling import osc_sampler
from .apps.dynamic_mapper import DynamicToolMapper
from .apps.midi_tools import register_midi_tools
from .routing.triggers import global_trigger_engine

# Set up logging
logger = logging.getLogger(__name__)

# Create FastMCP instance with conversational capabilities
server = FastMCP("OSC-MCP")

# Register MIDI Bridge tools on server
register_midi_tools(server)

# Setup Reactive Triggers server reference
global_trigger_engine.set_server(server)

# Instantiate Dynamic OSCQuery Mapper
dynamic_mapper = DynamicToolMapper(server)

@server.lifespan()
async def lifespan(app):
    # Startup
    logger.info("OSC-MCP Lifespan: starting discovery mapper...")
    await dynamic_mapper.start()
    yield
    # Shutdown
    logger.info("OSC-MCP Lifespan: stopping discovery mapper...")
    await dynamic_mapper.stop()

# Import legacy/integration tools from mcp_server
from . import mcp_server

# Store OSC server instances and transports for cleanup
_osc_transports: List[Any] = []


# Pydantic models for input validation (FastMCP 2.13)
class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""

    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(..., pattern=r"^/.*", description="OSC address pattern starting with /")
    values: List[Any] = Field(..., description="List of values to send")


class OSCListenerInput(BaseModel):
    """Input model for starting OSC listener."""

    port: int = Field(..., gt=0, le=65535, description="UDP port to listen on (1-65535)")
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")


class OSCEchoTestInput(BaseModel):
    """Input model for OSC echo test."""

    port: int = Field(default=9000, gt=0, le=65535, description="Test port to use (1-65535)")


# FastMCP 2.14.3 Resource Management
# Automatic resource cleanup is handled by FastMCP server lifecycle
# OSC transports are managed through the global _osc_transports list


@server.tool()
async def send_osc_message(
    host: str, port: int, address: str, values: List[Any], ctx: Context
) -> Dict[str, Any]:
    """Send OSC message to target application with conversational guidance.

    This tool sends OSC messages and provides intelligent follow-up suggestions
    for building complex automation workflows.

    Args:
        host: Target host IP address
        port: Target port number
        address: OSC address pattern (e.g., "/volume")
        values: List of values to send (will be converted to appropriate OSC types)
        ctx: FastMCP Context for native client-side LLM sampling
    """
    try:
        client = SimpleUDPClient(host, port)
        client.send_message(address, values)
        logger.info("Sent OSC message to %s:%s - %s: %s", host, port, address, values)

        # Validate the message using LLM sampling
        validation = await osc_sampler.validate_osc_message(address, values, ctx)

        # Generate conversational response
        response = {
            "status": "success",
            "message": "OSC message sent successfully",
            "host": host,
            "port": port,
            "address": address,
            "values": values,
            "validation": validation,
            "conversational": {
                "next_steps": [
                    f"Consider setting up a listener on port {port} to monitor responses",
                    "You could create a batch of related messages for this workflow",
                    "Try the generate_osc_workflow tool for complex automation sequences",
                ],
                "related_tools": ["start_osc_listener", "generate_osc_workflow", "test_osc_echo"],
                "suggestions": validation.get("suggestions", []),
            },
        }

        return response

    except Exception as e:
        error_msg = f"Failed to send OSC message: {e!s}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "host": host,
            "port": port,
            "address": address,
            "values": values,
            "conversational": {
                "troubleshooting": [
                    "Check if the target application is running and listening on the specified port",
                    "Verify the OSC address pattern matches what the application expects",
                    "Try using test_osc_echo first to verify basic OSC connectivity",
                ],
                "related_tools": ["test_osc_echo", "start_osc_listener"],
            },
        }


@server.tool()
async def start_osc_listener(port: int, address: str = "0.0.0.0") -> Dict[str, Any]:
    """Start OSC server to receive messages.

    Args:
        port: Port to listen on
        address: Interface address to bind to (default: "0.0.0.0" for all interfaces)

    Returns:
        Dictionary with server status and information
    """
    # Create dispatcher and server
    osc_dispatcher = dispatcher.Dispatcher()

    # Default handler for all messages
    def default_handler(addr: str, *args: Any) -> None:
        """Handle incoming OSC messages."""
        logger.info(f"Received OSC message: {addr} {args}")
        # Process message in reactive triggers
        global_trigger_engine.handle_message(addr, args)

    # Set default handler for all addresses
    osc_dispatcher.set_default_handler(default_handler)

    try:
        # Create and start the server in a non-blocking way
        server = osc_server.AsyncIOOSCUDPServer(
            (address, port), osc_dispatcher, asyncio.get_event_loop()
        )

        # Start the server in the background
        transport, _ = await server.create_serve_endpoint()

        # Store transport for cleanup during server shutdown
        _osc_transports.append(transport)

        logger.info(f"OSC server started on {address}:{port}")

        return {
            "status": "success",
            "message": "OSC server started successfully",
            "address": address,
            "port": port,
            "transport": str(
                transport
            ),  # For reference, actual transport object can't be serialized
        }

    except Exception as e:
        error_msg = f"Failed to start OSC server: {e!s}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "address": address,
            "port": port,
        }


# Add a simple test function to verify the server is working
@server.tool()
async def generate_osc_workflow(
    workflow_description: str,
    ctx: Context,
    target_application: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> Dict[str, Any]:
    """Generate a complete OSC automation workflow using AI sampling.

    This tool uses LLM sampling to intelligently design OSC workflows for
    complex automation tasks, providing step-by-step message sequences
    and conversational guidance.

    Args:
        workflow_description: Natural language description of the desired workflow
        ctx: FastMCP Context for native client-side LLM sampling
        target_application: Target application name (optional, for better suggestions)
        host: Default target host
        port: Default target port
    """
    try:
        # Use sampling to generate the workflow
        workflow = await osc_sampler.generate_osc_workflow(
            workflow_description, ctx, [target_application] if target_application else None
        )

        # Enhance with conversational elements
        response = {
            "status": "success",
            "message": f"Generated OSC workflow for: {workflow_description}",
            "workflow": workflow,
            "conversational": {
                "implementation_steps": [
                    "Review the generated message sequence and timing",
                    "Test individual messages using send_osc_message",
                    "Run the workflow using execute_osc_workflow",
                    "Monitor results with start_osc_listener if needed",
                ],
                "related_tools": ["execute_osc_workflow", "send_osc_message", "start_osc_listener"],
                "validation_suggestions": workflow.get("validation_notes", []),
            },
        }

        return response

    except Exception as e:
        error_msg = f"Failed to generate OSC workflow: {e!s}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "workflow_description": workflow_description,
            "conversational": {
                "troubleshooting": [
                    "Try providing more specific details about the target application",
                    "Include specific parameter ranges or timing requirements",
                    "Check if the workflow description is clear and actionable",
                ],
                "related_tools": ["send_osc_message", "test_osc_echo"],
            },
        }


@server.tool()
async def execute_osc_workflow(
    workflow_data: Dict[str, Any], ctx: Context, validate_first: bool = True
) -> Dict[str, Any]:
    """Execute a generated OSC workflow with intelligent validation.

    This tool runs complete OSC automation sequences with real-time
    validation and conversational feedback during execution.

    Args:
        workflow_data: Workflow dictionary from generate_osc_workflow
        ctx: FastMCP Context for native client-side LLM sampling
        validate_first: Whether to validate workflow before execution
    """
    try:
        # Validate workflow if requested
        if validate_first:
            validation = await osc_sampler.validate_osc_workflow(workflow_data, ctx)
            if not validation.get("valid", False):
                return {
                    "status": "validation_failed",
                    "message": "Workflow validation failed",
                    "validation": validation,
                    "conversational": {
                        "next_steps": validation.get("fix_suggestions", []),
                        "related_tools": ["generate_osc_workflow"],
                    },
                }

        # Execute the workflow
        execution_result = await osc_sampler.execute_osc_workflow(workflow_data)

        # Generate conversational response
        response = {
            "status": "success" if execution_result.get("success") else "execution_failed",
            "message": f"Workflow execution {'succeeded' if execution_result.get('success') else 'failed'}",
            "execution": execution_result,
            "conversational": {
                "analysis": execution_result.get("analysis", {}),
                "next_steps": [
                    "Review execution timing and results",
                    "Consider saving this workflow for reuse",
                    "Monitor target application for expected changes",
                ]
                if execution_result.get("success")
                else [
                    "Check OSC connectivity with test_osc_echo",
                    "Verify target application is running",
                    "Review workflow parameters and timing",
                ],
                "related_tools": ["generate_osc_workflow", "test_osc_echo", "save_osc_workflow"],
            },
        }

        return response

    except Exception as e:
        error_msg = f"Failed to execute OSC workflow: {e!s}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "conversational": {
                "troubleshooting": [
                    "Ensure workflow_data is properly formatted",
                    "Check OSC connectivity with test_osc_echo",
                    "Verify all required workflow parameters are present",
                ],
                "related_tools": ["generate_osc_workflow", "test_osc_echo"],
            },
        }


@server.tool()
async def test_osc_echo(ctx: Context, port: int = 9000) -> Dict[str, Any]:
    """Test OSC functionality with conversational guidance and intelligent validation.

    This enhanced test function uses LLM sampling to validate OSC connectivity
    and provides detailed troubleshooting guidance.

    Args:
        ctx: FastMCP Context for native client-side LLM sampling
        port: Test port to use (default: 9000)
    """
    # Start the server
    server_result = await start_osc_listener(port)
    if server_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Failed to start test server: {server_result['message']}",
            "conversational": {
                "troubleshooting": [
                    "Check if port is already in use",
                    "Verify network permissions",
                    "Try a different port number",
                ],
                "related_tools": ["start_osc_listener"],
            },
        }

    # Send a test message
    test_address = "/test/echo"
    test_values = [1, 2.0, "three", True]

    send_result = await send_osc_message("127.0.0.1", port, test_address, test_values, ctx)
    if send_result["status"] != "success":
        return {
            "status": "error",
            "message": f"Failed to send test message: {send_result['message']}",
            "conversational": {
                "troubleshooting": [
                    "Check firewall settings",
                    "Verify OSC server started properly",
                    "Try different host/port combination",
                ],
                "related_tools": ["send_osc_message", "start_osc_listener"],
            },
        }

    # Use LLM sampling to analyze the test
    test_analysis = await osc_sampler.analyze_osc_test(server_result, send_result, ctx)

    # Generate comprehensive conversational response
    return {
        "status": "success",
        "message": "OSC echo test completed successfully",
        "test_address": test_address,
        "test_values": test_values,
        "server": server_result,
        "send_result": send_result,
        "analysis": test_analysis,
        "conversational": {
            "summary": test_analysis.get("summary", "OSC connectivity verified"),
            "next_steps": [
                "Try sending messages to your target application",
                "Use generate_osc_workflow for complex automation",
                "Set up listeners for bidirectional communication",
            ],
            "related_tools": ["send_osc_message", "generate_osc_workflow", "start_osc_listener"],
            "confidence_level": test_analysis.get("confidence", "high"),
        },
    }


@server.tool()
async def list_arazzo_workflows() -> Dict[str, Any]:
    """List all available Arazzo mission descriptors in this server.

    Returns:
        Dictionary containing available workflows and their metadata.
    """
    workflows_dir = Path(__file__).parent / "workflows"
    if not workflows_dir.exists():
        return {"status": "success", "workflows": [], "message": "No workflows directory found"}

    found_workflows = []
    for yaml_file in workflows_dir.glob("*.yaml"):
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
                found_workflows.append(
                    {
                        "id": yaml_file.stem,
                        "title": data.get("info", {}).get("title"),
                        "description": data.get("info", {}).get("description"),
                        "spec": data,
                    }
                )
        except Exception as e:
            logger.error(f"Error parsing workflow {yaml_file}: {e}")

    return {"status": "success", "count": len(found_workflows), "workflows": found_workflows}


@server.tool()
async def oscquery_list_services() -> Dict[str, Any]:
    """List dynamically discovered OSCQuery devices on the local network."""
    try:
        services = dynamic_mapper.get_services()
        return {"status": "success", "count": len(services), "services": services}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def oscquery_get_parameters(service_name: str) -> Dict[str, Any]:
    """Retrieve full parameter tree for a discovered OSCQuery device.

    Args:
        service_name: Name of the discovered service.
    """
    try:
        params = await dynamic_mapper.get_service_parameters(service_name)
        return {"status": "success", "count": len(params), "parameters": params}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def register_reactive_trigger(
    address_pattern: str,
    target_tool: str,
    args_template: Dict[str, Any]
) -> Dict[str, Any]:
    """Register an event action triggering an MCP tool when an OSC message matches a pattern.

    Args:
        address_pattern: Glob pattern to match incoming OSC addresses (e.g. '/live/beat', '/vco/*')
        target_tool: Tool name to execute (e.g. 'send_osc_message', 'execute_osc_workflow')
        args_template: Arguments dictionary matching target tool schema. Supports variable substitution (e.g. {"value": "$value", "port": "$0"})
    """
    try:
        global_trigger_engine.register_trigger(address_pattern, target_tool, args_template)
        return {
            "status": "success",
            "message": f"Successfully mapped incoming {address_pattern} to execute {target_tool}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def get_reactive_triggers() -> Dict[str, Any]:
    """Retrieve list of all active reactive trigger actions."""
    try:
        triggers = global_trigger_engine.get_triggers()
        return {"status": "success", "count": len(triggers), "triggers": triggers}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def remove_reactive_trigger(address_pattern: str) -> Dict[str, Any]:
    """Remove a reactive trigger action matching the specified pattern."""
    try:
        global_trigger_engine.remove_trigger(address_pattern)
        return {"status": "success", "message": f"Removed trigger for pattern {address_pattern}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def trigger_vrchat_haptic_lfo(
    device: str = "both",
    pattern: str = "sine",
    duration: float = 2.0,
    frequency_hz: float = 2.0
) -> Dict[str, Any]:
    """Trigger VRChat haptic feedback modulated by an LFO waveform.

    Args:
        device: Haptic output device - 'left', 'right', or 'both'
        pattern: Waveform pattern - 'sine', 'sawtooth', or 'square'
        duration: Pulse train duration in seconds (default: 2.0)
        frequency_hz: Modulation frequency in Hz (default: 2.0)
    """
    import math
    steps = int(duration * 30)
    interval = 1.0 / 30.0

    async def run_pattern():
        from .apps.vrchat import VRChatOSC
        client = VRChatOSC()
        # VRChat input_port/output_port match defaults
        await client.start()
        
        for step in range(steps):
            t = step * interval
            phase = 2 * math.pi * frequency_hz * t
            
            if pattern == "sine":
                amplitude = (math.sin(phase) + 1.0) / 2.0
            elif pattern == "sawtooth":
                amplitude = (t * frequency_hz) % 1.0
            elif pattern == "square":
                amplitude = 1.0 if (t * frequency_hz) % 1.0 < 0.5 else 0.0
            else:
                amplitude = 0.5
                
            client.trigger_haptic(device=device, duration=interval, amplitude=amplitude)
            await asyncio.sleep(interval)
            
        await client.stop()

    asyncio.create_task(run_pattern())
    return {
        "status": "success",
        "message": f"Started haptic LFO pattern '{pattern}' on {device} for {duration}s"
    }


@server.tool()
async def set_vrchat_expression(
    expression: str,
    intensity: float = 1.0
) -> Dict[str, Any]:
    """Set VRChat avatar Unified Expressions (face/eye tracking) parameters.

    Args:
        expression: Expression name (e.g. 'EyeLidLeft', 'JawOpen', 'Smile')
        intensity: Expression intensity scale from 0.0 to 1.0 (default: 1.0)
    """
    from .apps.vrchat import VRChatOSC
    try:
        vr = VRChatOSC()
        # VRChat Unified Expressions namespace mapping (v2)
        param_name = f"FT/v2/{expression}"
        vr.set_parameter(param_name, intensity)
        return {
            "status": "success",
            "parameter": param_name,
            "intensity": intensity
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set expression: {e}"}


# FastMCP 3.4.2 Native Prompts
PROMPTS_DIR = Path(__file__).parent.parent.parent / "assets" / "prompts"

def read_prompt_file(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    alt_path = Path(__file__).parent.parent / "assets" / "prompts" / f"{name}.md"
    if alt_path.exists():
        return alt_path.read_text(encoding="utf-8")
    return f"Prompt {name} not found"

@server.prompt(description="Core system prompts for guiding LLM interactions with OSC-MCP")
def system() -> str:
    return read_prompt_file("system")

@server.prompt(description="Prompts for managing dynamic OSC contents and parameters")
def content_management() -> str:
    return read_prompt_file("content_management")

@server.prompt(description="Prompts for designing and executing multi-step OSC workflows")
def workflow_automation() -> str:
    return read_prompt_file("workflow_automation")

@server.prompt(description="Guidelines and specs for integrating with third-party software")
def platform_integration() -> str:
    return read_prompt_file("platform_integration")

@server.prompt(description="Troubleshooting checklists and networking guides")
def troubleshooting() -> str:
    return read_prompt_file("troubleshooting")


# FastMCP 3.4.2 Prefab UI Components
from prefab_ui.app import PrefabApp
from prefab_ui.components import DataTable, DataTableColumn

@server.tool(app=True)
def show_active_mappings() -> PrefabApp:
    """Display an interactive data table of active MIDI and reactive trigger mappings."""
    from .routing.triggers import global_trigger_engine
    from .apps.midi_tools import _active_bridge

    mappings_data = []

    # Add reactive triggers
    for t in global_trigger_engine.get_triggers():
        mappings_data.append({
            "type": "Reactive Trigger",
            "source": t["pattern"],
            "target": t["tool"],
            "details": str(t["template"])
        })

    # Add MIDI mappings
    if _active_bridge:
        for m in _active_bridge.midi_to_osc_mappings:
            mappings_data.append({
                "type": "MIDI -> OSC",
                "source": f"Ch {m.channel} CC {m.control}",
                "target": m.osc_address,
                "details": f"Range: {m.osc_range}"
            })
        for addr, mappings in _active_bridge.osc_to_midi_mappings.items():
            for m in mappings:
                mappings_data.append({
                    "type": "OSC -> MIDI",
                    "source": addr,
                    "target": f"Ch {m.channel} CC {m.control}",
                    "details": f"Range: {m.midi_range}"
                })

    if not mappings_data:
        mappings_data = [{"type": "None", "source": "N/A", "target": "N/A", "details": "No active mappings found"}]

    with PrefabApp() as app:
        DataTable(
            data=mappings_data,
            columns=[
                DataTableColumn(name="type", label="Mapping Type"),
                DataTableColumn(name="source", label="Source Signal"),
                DataTableColumn(name="target", label="Target Destination"),
                DataTableColumn(name="details", label="Configuration Details")
            ]
        )
    return app


@server.tool(app=True)
def show_discovered_devices() -> PrefabApp:
    """Display an interactive data table of discovered OSCQuery devices on the network."""
    services = dynamic_mapper.get_services()
    
    data = []
    for s in services:
        data.append({
            "name": s.get("name", "Unknown"),
            "host": s.get("host", "N/A"),
            "osc_port": str(s.get("osc_port", "N/A")),
            "ws_port": str(s.get("ws_port", "N/A"))
        })
        
    if not data:
        data = [{"name": "None", "host": "N/A", "osc_port": "N/A", "ws_port": "N/A"}]
        
    with PrefabApp() as app:
        DataTable(
            data=data,
            columns=[
                DataTableColumn(name="name", label="Device Name"),
                DataTableColumn(name="host", label="IP Address"),
                DataTableColumn(name="osc_port", label="OSC Port"),
                DataTableColumn(name="ws_port", label="OSCQuery WS Port")
            ]
        )
    return app


@server.tool(app=True)
def show_recent_messages(port: int, limit: int = 20) -> PrefabApp:
    """Display an interactive data table of recently received OSC messages on a port."""
    from .mcp_server import osc_servers
    
    data = []
    if port in osc_servers:
        osc_server_instance = osc_servers[port]
        messages = osc_server_instance.get_received_messages(limit=limit)
        for idx, m in enumerate(messages):
            import datetime
            time_str = datetime.datetime.fromtimestamp(m.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
            data.append({
                "time": time_str,
                "address": m.get("address", "N/A"),
                "values": str(m.get("args", [])),
                "age": f"{m.get('age_seconds', 0.0):.2f}s"
            })
            
    if not data:
        data = [{"time": "N/A", "address": "N/A", "values": "[]", "age": "N/A"}]
        
    with PrefabApp() as app:
        DataTable(
            data=data,
            columns=[
                DataTableColumn(name="time", label="Timestamp"),
                DataTableColumn(name="address", label="OSC Address"),
                DataTableColumn(name="values", label="Values"),
                DataTableColumn(name="age", label="Age")
            ]
        )
    return app


@server.tool(app=True)
def show_available_workflows() -> PrefabApp:
    """Display an interactive data table of available Arazzo automation workflows."""
    workflows_dir = Path(__file__).parent / "workflows"
    found_workflows = []
    if workflows_dir.exists():
        for yaml_file in workflows_dir.glob("*.yaml"):
            try:
                import yaml
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)
                    info = data.get("info", {})
                    # Count steps/actions
                    steps = len(data.get("workflows", {}).get("test_run", {}).get("steps", []))
                    found_workflows.append({
                        "id": yaml_file.stem,
                        "title": info.get("title", yaml_file.stem),
                        "description": info.get("description", "No description provided"),
                        "steps": str(steps)
                    })
            except Exception:
                pass
                
    if not found_workflows:
        found_workflows = [{"id": "None", "title": "N/A", "description": "No workflows found", "steps": "0"}]
        
    with PrefabApp() as app:
        DataTable(
            data=found_workflows,
            columns=[
                DataTableColumn(name="id", label="Workflow ID"),
                DataTableColumn(name="title", label="Workflow Title"),
                DataTableColumn(name="description", label="Description Summary"),
                DataTableColumn(name="steps", label="Steps Count")
            ]
        )
    return app


# ASGI app for uvicorn (web_sota/start.ps1): uvicorn oscmcp.server:app
app = server.http_app()


# FastMCP 2.14.3 Server Runner
# This allows running the server directly with: python -m oscmcp.server
if __name__ == "__main__":
    import asyncio
    import sys

    async def cleanup_resources():
        """Clean up OSC resources on shutdown."""
        logger.info("OSC-MCP server shutting down - cleaning up resources")

        # Close all OSC server transports
        for idx, transport in enumerate(_osc_transports):
            try:
                transport.close()
                logger.info(f"Closed OSC transport {idx}")
            except Exception as e:
                logger.error(f"Error closing OSC transport {idx}: {e}")

        # Clear all resources
        _osc_transports.clear()
        logger.info("OSC-MCP server cleanup complete")

    try:
        # Use FastMCP 2.14.3 built-in server with conversational capabilities
        if len(sys.argv) > 1 and sys.argv[1] == "http":
            # HTTP transport mode with sampling and conversational features
            server.run(
                transport="streamable-http",
                host="0.0.0.0",
                port=8000,
            )
        else:
            # Default: stdio transport (for MCP clients like Cursor)
            server.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully...")
        asyncio.run(cleanup_resources())
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        asyncio.run(cleanup_resources())
        sys.exit(1)
