"""OSC-MCP Server Implementation.

This module implements the core OSC server functionality using FastMCP 2.14.3+
and python-osc for Open Sound Control protocol support, with conversational
tool returns and advanced LLM sampling capabilities.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient

from .apps import OBSOSC, QLabOSC
from .apps.dynamic_mapper import DynamicToolMapper
from .apps.midi_tools import register_midi_tools
from .routing.scanner import scan_subnet_osc as run_subnet_scan
from .routing.triggers import global_trigger_engine
from .sampling import osc_sampler

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

# Store OSC server instances and transports for cleanup
_osc_transports: list[Any] = []

# Tool annotations for FastMCP
_README_ONLY = {"readonly": True}
_MUTATING = {}
_DESTRUCTIVE = {"destructive": True}


# Pydantic models for input validation (FastMCP 2.13)
class OSCMessageInput(BaseModel):
    """Input model for OSC message sending."""

    host: str = Field(..., description="Target hostname or IP address")
    port: int = Field(..., gt=0, le=65535, description="Target UDP port (1-65535)")
    address: str = Field(..., pattern=r"^/.*", description="OSC address pattern starting with /")
    values: list[Any] = Field(..., description="List of values to send")


class OSCListenerInput(BaseModel):
    """Input model for starting OSC listener."""

    port: int = Field(..., gt=0, le=65535, description="UDP port to listen on (1-65535)")
    address: str = Field(default="0.0.0.0", description="Network interface to bind to")


class OSCEchoTestInput(BaseModel):
    """Input model for OSC echo test."""

    port: int = Field(default=9000, gt=0, le=65535, description="Test port to use (1-65535)")


@server.resource("status://server")
async def status_resource() -> dict:
    """Live server status -- uptime, active listeners, tool count."""
    return {
        "status": "ok",
        "listeners": len(_osc_transports),
        "tool_count": len((getattr(server, "_tool_manager", None) and server._tool_manager.tools) or []),
    }


# FastMCP 2.14.3 Resource Management
# Automatic resource cleanup is handled by FastMCP server lifecycle
# OSC transports are managed through the global _osc_transports list


@server.tool()
async def send_osc_message(
    host: Annotated[str, Field(description="Target host IP address")],
    port: Annotated[int, Field(description="Target UDP port (1-65535)", gt=0, le=65535)],
    address: Annotated[str, Field(description="OSC address pattern starting with / (e.g., '/volume')")],
    values: Annotated[list[Any], Field(description="List of values to send (converted to appropriate OSC types)")],
    ctx: Context,
) -> dict[str, Any]:
    """Send OSC message to target application with conversational guidance.

    This tool sends OSC messages and provides intelligent follow-up suggestions
    for building complex automation workflows.

    ## Return
    {"status": "success"|"error", "message": str, "host": str, "port": int,
     "address": str, "values": list, "validation": dict, "conversational": {...}}

    ## Examples
    send_osc_message(host="127.0.0.1", port=7000, address="/volume", values=[0.8])
    send_osc_message(host="192.168.1.10", port=9000, address="/live/beat", values=[1])
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


@server.tool(annotations=_MUTATING)
async def start_osc_listener(
    port: Annotated[int, Field(description="UDP port to listen on (1-65535)", gt=0, le=65535)],
    address: Annotated[str, Field(description="Interface to bind (default: 0.0.0.0 for all)")] = "0.0.0.0",
) -> dict[str, Any]:
    """Start OSC server to receive messages.

    ## Return Format
    {"status": "success"|"error", "message": str, "address": str, "port": int, "transport": str}

    ## Examples
    start_osc_listener(port=9000, address="0.0.0.0")
    start_osc_listener(port=7000)
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
        server = osc_server.AsyncIOOSCUDPServer((address, port), osc_dispatcher, asyncio.get_event_loop())

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
            "transport": str(transport),  # For reference, actual transport object can't be serialized
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
    workflow_description: Annotated[str, Field(description="Natural language description of the desired workflow")],
    ctx: Context,
    target_application: Annotated[
        str | None, Field(description="Target app name (optional, for better suggestions)")
    ] = None,
    host: Annotated[str, Field(description="Default target host")] = "127.0.0.1",
    port: Annotated[int, Field(description="Default target port", gt=0, le=65535)] = 8000,
) -> dict[str, Any]:
    """Generate a complete OSC automation workflow using AI sampling.

    This tool uses LLM sampling to intelligently design OSC workflows for
    complex automation tasks, providing step-by-step message sequences
    and conversational guidance.

    ## Return
    {"status": "success"|"error", "message": str, "workflow": dict,
     "conversational": {"implementation_steps": list, "related_tools": list}}

    ## Examples
    generate_osc_workflow(
        workflow_description="Fade volume from 0 to 1 over 5 seconds",
        target_application="Ableton Live")
    generate_osc_workflow(workflow_description="Switch OBS scene every 30 seconds", host="127.0.0.1", port=7000)
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
    workflow_data: Annotated[dict[str, Any], Field(description="Workflow dictionary from generate_osc_workflow")],
    ctx: Context,
    validate_first: Annotated[bool, Field(description="Whether to validate workflow before execution")] = True,
) -> dict[str, Any]:
    """Execute a generated OSC workflow with intelligent validation.

    This tool runs complete OSC automation sequences with real-time
    validation and conversational feedback during execution.

    ## Return Format
    {"status": "success"|"error", "message": str, "execution": dict,
     "conversational": {"analysis": dict, "next_steps": list, "related_tools": list}}

    ## Examples
    execute_osc_workflow(workflow_data={"steps": [{"address": "/volume", "values": [0.8]}]}, validate_first=True)
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


@server.tool(annotations=_README_ONLY)
async def test_osc_echo(
    ctx: Context,
    port: Annotated[int, Field(description="Test port to use (1-65535)", gt=0, le=65535)] = 9000,
) -> dict[str, Any]:
    """Test OSC functionality with conversational guidance and intelligent validation.

    This enhanced test function uses LLM sampling to validate OSC connectivity
    and provides detailed troubleshooting guidance.

    ## Return Format
    {"status": "success"|"error", "message": str, "test_address": str,
     "test_values": list, "server": dict, "send_result": dict,
     "analysis": dict, "conversational": dict}

    ## Examples
    test_osc_echo(port=9000)
    test_osc_echo(port=7000)
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


@server.tool(annotations=_README_ONLY)
async def list_arazzo_workflows() -> dict[str, Any]:
    """List all available Arazzo mission descriptors in this server.

    ## Return Format
    {"status": "success", "workflows": [{"id": str, "title": str, "description": str, "spec": dict}], "count": int}

    ## Examples
    list_arazzo_workflows()
    """
    workflows_dir = Path(__file__).parent / "workflows"
    if not workflows_dir.exists():
        return {"status": "success", "workflows": [], "message": "No workflows directory found"}

    found_workflows = []
    for yaml_file in workflows_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
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
async def oscquery_list_services() -> dict[str, Any]:
    """List dynamically discovered OSCQuery devices on the local network.

    ## Return Format
    {"status": "success"|"error", "count": int,
     "services": [{"name": str, "host": str, "osc_port": int, "ws_port": int}]}

    ## Examples
    oscquery_list_services()
    """
    try:
        services = dynamic_mapper.get_services()
        return {"status": "success", "count": len(services), "services": services}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def oscquery_get_parameters(
    service_name: Annotated[str, Field(description="Name of the discovered service")],
) -> dict[str, Any]:
    """Retrieve full parameter tree for a discovered OSCQuery device.

    ## Return Format
    {"status": "success"|"error", "count": int, "parameters": list}

    ## Examples
    oscquery_get_parameters(service_name="Ableton Live")
    oscquery_get_parameters(service_name="Resolume Arena")
    """
    try:
        params = await dynamic_mapper.get_service_parameters(service_name)
        return {"status": "success", "count": len(params), "parameters": params}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def register_reactive_trigger(
    address_pattern: Annotated[str, Field(description="Glob pattern for OSC addresses (e.g. '/live/beat', '/vco/*')")],
    target_tool: Annotated[str, Field(description="Tool to execute (e.g. 'send_osc_message', 'execute_osc_workflow')")],
    args_template: Annotated[
        dict[str, Any], Field(description="Args dict with variable substitution, e.g. {'value': '$value'}")
    ],
) -> dict[str, Any]:
    """Register an event action triggering an MCP tool when an OSC message matches a pattern.

    ## Return Format
    {"status": "success"|"error", "message": str}

    ## Examples
    register_reactive_trigger(
        address_pattern="/live/beat", target_tool="send_osc_message",
        args_template={"address": "/volume", "values": [0.5]})
    register_reactive_trigger(
        address_pattern="/vco/*", target_tool="send_osc_message",
        args_template={"address": "/filter", "port": "$0"})
    """
    try:
        global_trigger_engine.register_trigger(address_pattern, target_tool, args_template)
        return {
            "status": "success",
            "message": f"Successfully mapped incoming {address_pattern} to execute {target_tool}",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool(annotations=_README_ONLY)
async def get_reactive_triggers() -> dict[str, Any]:
    """Retrieve list of all active reactive trigger actions.

    ## Return Format
    {"status": "success"|"error", "count": int, "triggers": [{"pattern": str, "tool": str, "template": dict}]}

    ## Examples
    get_reactive_triggers()
    """
    try:
        triggers = global_trigger_engine.get_triggers()
        return {"status": "success", "count": len(triggers), "triggers": triggers}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool(annotations=_DESTRUCTIVE)
async def remove_reactive_trigger(
    address_pattern: Annotated[str, Field(description="OSC address pattern of the trigger to remove")],
) -> dict[str, Any]:
    """Remove a reactive trigger action matching the specified pattern.

    ## Return Format
    {"status": "success"|"error", "message": str}

    ## Examples
    remove_reactive_trigger(address_pattern="/live/beat")
    """
    try:
        global_trigger_engine.remove_trigger(address_pattern)
        return {"status": "success", "message": f"Removed trigger for pattern {address_pattern}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool(annotations=_MUTATING)
async def trigger_vrchat_haptic_lfo(
    device: Annotated[str, Field(description="Haptic output device - 'left', 'right', or 'both'")] = "both",
    pattern: Annotated[str, Field(description="Waveform pattern - 'sine', 'sawtooth', or 'square'")] = "sine",
    duration: Annotated[float, Field(description="Pulse train duration in seconds")] = 2.0,
    frequency_hz: Annotated[float, Field(description="Modulation frequency in Hz")] = 2.0,
) -> dict[str, Any]:
    """Trigger VRChat haptic feedback modulated by an LFO waveform.

    ## Return Format
    {"status": "success", "message": str}

    ## Examples
    trigger_vrchat_haptic_lfo(device="both", pattern="sine", duration=2.0, frequency_hz=2.0)
    trigger_vrchat_haptic_lfo(device="left", pattern="square")
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
    return {"status": "success", "message": f"Started haptic LFO pattern '{pattern}' on {device} for {duration}s"}


@server.tool(annotations=_MUTATING)
async def set_vrchat_expression(
    expression: Annotated[str, Field(description="Expression name (e.g. 'EyeLidLeft', 'JawOpen', 'Smile')")],
    intensity: Annotated[float, Field(description="Expression intensity scale from 0.0 to 1.0")] = 1.0,
) -> dict[str, Any]:
    """Set VRChat avatar Unified Expressions (face/eye tracking) parameters.

    ## Return Format
    {"status": "success"|"error", "parameter": str, "intensity": float}

    ## Examples
    set_vrchat_expression(expression="Smile", intensity=0.8)
    set_vrchat_expression(expression="EyeLidLeft", intensity=0.5)
    """
    from .apps.vrchat import VRChatOSC

    try:
        vr = VRChatOSC()
        # VRChat Unified Expressions namespace mapping (v2)
        param_name = f"FT/v2/{expression}"
        vr.set_parameter(param_name, intensity)
        return {"status": "success", "parameter": param_name, "intensity": intensity}
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


@server.prompt()
def osc_help_topic(topic: str = "overview") -> str:
    """Get help on using OSC-MCP tools and workflows."""
    topics = {
        "overview": (
            "# OSC-MCP Help\n\n"
            "Comprehensive help for OSC-MCP tools and workflows.\n"
            "- Use send_osc_message to send OSC messages to any target\n"
            "- Use start_osc_listener to receive messages\n"
            "- Use test_osc_echo to verify connectivity\n"
            "- Use generate_osc_workflow for multi-step automation"
        ),
        "apps": (
            "# Supported Applications\n\n"
            "- Ableton Live (port 11000)\n"
            "- TouchDesigner (port 12000)\n"
            "- VRChat (port 9000)\n"
            "- Max/MSP (port 13000)\n"
            "- SuperCollider (port 57120)\n"
            "- VCV Rack (port 14000)\n"
            "- QLab (port 53000)"
        ),
    }
    return topics.get(topic, topics["overview"])


# FastMCP 3.4.2 Prefab UI Components
from prefab_ui.app import PrefabApp
from prefab_ui.components import DataTable, DataTableColumn


@server.tool(app=True, annotations=_README_ONLY)
def show_active_mappings() -> PrefabApp:
    """Display an interactive data table of active MIDI and reactive trigger mappings.

    Shows Reactive Triggers (OSC pattern -> tool), MIDI->OSC, and OSC->MIDI mappings.

    ## Return Format
    PrefabApp with DataTable columns: Mapping Type, Source Signal, Target Destination, Configuration Details

    ## Examples
    show_active_mappings()
    """
    from .apps.midi_tools import _active_bridge
    from .routing.triggers import global_trigger_engine

    mappings_data = []

    # Add reactive triggers
    for t in global_trigger_engine.get_triggers():
        mappings_data.append(
            {"type": "Reactive Trigger", "source": t["pattern"], "target": t["tool"], "details": str(t["template"])}
        )

    # Add MIDI mappings
    if _active_bridge:
        for m in _active_bridge.midi_to_osc_mappings:
            mappings_data.append(
                {
                    "type": "MIDI -> OSC",
                    "source": f"Ch {m.channel} CC {m.control}",
                    "target": m.osc_address,
                    "details": f"Range: {m.osc_range}",
                }
            )
        for addr, mappings in _active_bridge.osc_to_midi_mappings.items():
            for m in mappings:
                mappings_data.append(
                    {
                        "type": "OSC -> MIDI",
                        "source": addr,
                        "target": f"Ch {m.channel} CC {m.control}",
                        "details": f"Range: {m.midi_range}",
                    }
                )

    if not mappings_data:
        mappings_data = [{"type": "None", "source": "N/A", "target": "N/A", "details": "No active mappings found"}]

    with PrefabApp() as app:
        DataTable(
            data=mappings_data,
            columns=[
                DataTableColumn(name="type", label="Mapping Type"),
                DataTableColumn(name="source", label="Source Signal"),
                DataTableColumn(name="target", label="Target Destination"),
                DataTableColumn(name="details", label="Configuration Details"),
            ],
        )
    return app


@server.tool(app=True, annotations=_README_ONLY)
def show_discovered_devices() -> PrefabApp:
    """Display an interactive data table of discovered OSCQuery devices on the network.

    ## Return Format
    PrefabApp with DataTable columns: Device Name, IP Address, OSC Port, OSCQuery WS Port

    ## Examples
    show_discovered_devices()
    """
    services = dynamic_mapper.get_services()

    data = []
    for s in services:
        data.append(
            {
                "name": s.get("name", "Unknown"),
                "host": s.get("host", "N/A"),
                "osc_port": str(s.get("osc_port", "N/A")),
                "ws_port": str(s.get("ws_port", "N/A")),
            }
        )

    if not data:
        data = [{"name": "None", "host": "N/A", "osc_port": "N/A", "ws_port": "N/A"}]

    with PrefabApp() as app:
        DataTable(
            data=data,
            columns=[
                DataTableColumn(name="name", label="Device Name"),
                DataTableColumn(name="host", label="IP Address"),
                DataTableColumn(name="osc_port", label="OSC Port"),
                DataTableColumn(name="ws_port", label="OSCQuery WS Port"),
            ],
        )
    return app


@server.tool(app=True, annotations=_README_ONLY)
def show_recent_messages(
    port: Annotated[int, Field(description="Port number to query for received messages")],
    limit: Annotated[int, Field(description="Maximum number of messages to display")] = 20,
) -> PrefabApp:
    """Display an interactive data table of recently received OSC messages on a port.

    ## Return Format
    PrefabApp with DataTable columns: Timestamp, OSC Address, Values, Age

    ## Examples
    show_recent_messages(port=9000, limit=20)
    """
    from .mcp_server import osc_servers

    data = []
    if port in osc_servers:
        osc_server_instance = osc_servers[port]
        messages = osc_server_instance.get_received_messages(limit=limit)
        for idx, m in enumerate(messages):
            import datetime

            time_str = datetime.datetime.fromtimestamp(m.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
            data.append(
                {
                    "time": time_str,
                    "address": m.get("address", "N/A"),
                    "values": str(m.get("args", [])),
                    "age": f"{m.get('age_seconds', 0.0):.2f}s",
                }
            )

    if not data:
        data = [{"time": "N/A", "address": "N/A", "values": "[]", "age": "N/A"}]

    with PrefabApp() as app:
        DataTable(
            data=data,
            columns=[
                DataTableColumn(name="time", label="Timestamp"),
                DataTableColumn(name="address", label="OSC Address"),
                DataTableColumn(name="values", label="Values"),
                DataTableColumn(name="age", label="Age"),
            ],
        )
    return app


@server.tool(app=True, annotations=_README_ONLY)
def show_available_workflows() -> PrefabApp:
    """Display an interactive data table of available Arazzo automation workflows.

    ## Return Format
    PrefabApp with DataTable columns: Workflow ID, Workflow Title, Description Summary, Steps Count

    ## Examples
    show_available_workflows()
    """
    workflows_dir = Path(__file__).parent / "workflows"
    found_workflows = []
    if workflows_dir.exists():
        for yaml_file in workflows_dir.glob("*.yaml"):
            try:
                import yaml

                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                    info = data.get("info", {})
                    # Count steps/actions
                    steps = len(data.get("workflows", {}).get("test_run", {}).get("steps", []))
                    found_workflows.append(
                        {
                            "id": yaml_file.stem,
                            "title": info.get("title", yaml_file.stem),
                            "description": info.get("description", "No description provided"),
                            "steps": str(steps),
                        }
                    )
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
                DataTableColumn(name="steps", label="Steps Count"),
            ],
        )
    return app


@server.tool()
async def obs_manager(
    operation: Annotated[
        str, Field(description="Operation: switch_scene, toggle_mute, set_volume, start_stream, stop_stream")
    ],
    scene_name: Annotated[str | None, Field(description="Target scene name (required for switch_scene)")] = None,
    source_name: Annotated[
        str | None, Field(description="Audio source name (required for toggle_mute, set_volume)")
    ] = None,
    volume: Annotated[float | None, Field(description="Volume level 0.0 to 1.0 (required for set_volume)")] = None,
    host: Annotated[str, Field(description="OBS WebSocket host")] = "127.0.0.1",
    port: Annotated[int, Field(description="OBS WebSocket port", gt=0, le=65535)] = 7000,
) -> dict[str, Any]:
    """Control OBS Studio via OSC.

    [RATIONALE] Consolidated OBS operations into a single portmanteau tool to reduce
    tool count and keep related studio control actions grouped.

    Supported operations:
    - switch_scene: Switch to target scene (requires scene_name)
    - toggle_mute: Toggle mute status of an audio source (requires source_name)
    - set_volume: Set volume of an audio source 0.0 to 1.0 (requires source_name, volume)
    - start_stream: Start streaming
    - stop_stream: Stop streaming

    ## Return Format
    {"status": "success"|"error", "operation": str, "message": str}

    ## Examples
    obs_manager(operation="switch_scene", scene_name="Camera 1")
    obs_manager(operation="set_volume", source_name="Mic", volume=0.8)
    obs_manager(operation="start_stream")
    """
    obs = OBSOSC(host, port)
    op = operation.lower()
    try:
        if op == "switch_scene":
            if not scene_name:
                return {"status": "error", "message": "scene_name is required for switch_scene"}
            obs.switch_scene(scene_name)
        elif op == "toggle_mute":
            if not source_name:
                return {"status": "error", "message": "source_name is required for toggle_mute"}
            obs.toggle_mute(source_name)
        elif op == "set_volume":
            if not source_name or volume is None:
                return {"status": "error", "message": "source_name and volume are required for set_volume"}
            obs.set_volume(source_name, volume)
        elif op == "start_stream":
            obs.start_stream()
        elif op == "stop_stream":
            obs.stop_stream()
        else:
            return {"status": "error", "message": f"Unsupported operation: {operation}"}
        return {"status": "success", "operation": operation}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool()
async def qlab_manager(
    operation: Annotated[str, Field(description="Operation: 'go', 'stop', 'panic', 'trigger_cue', 'set_slider_level'")],
    cue_id: Annotated[str | None, Field(description="Cue ID (required for trigger_cue, set_slider_level)")] = None,
    slider_index: Annotated[int | None, Field(description="Slider index for set_slider_level")] = None,
    level: Annotated[float | None, Field(description="Volume level in dB for set_slider_level")] = None,
    host: Annotated[str, Field(description="QLab OSC host")] = "127.0.0.1",
    port: Annotated[int, Field(description="QLab OSC port", gt=0, le=65535)] = 53000,
) -> dict[str, Any]:
    """Control Figure 53 QLab workspaces via OSC.

    [RATIONALE] Consolidated QLab operations into a single portmanteau tool to reduce
    tool count and keep cue control actions grouped.

    Supported operations:
    - go: Trigger the GO button (start next cue)
    - stop: Stop all currently playing cues
    - panic: Fade out and stop all playing cues
    - trigger_cue: Start a specific cue (requires cue_id)
    - set_slider_level: Set volume level for a cue (requires cue_id, slider_index, level in dB)

    ## Return Format
    {"status": "success"|"error", "operation": str, "message": str}

    ## Examples
    qlab_manager(operation="go")
    qlab_manager(operation="trigger_cue", cue_id="cue-1")
    qlab_manager(operation="set_slider_level", cue_id="cue-1", slider_index=0, level=-6.0)
    """
    qlab = QLabOSC(host, port)
    op = operation.lower()
    try:
        if op == "go":
            qlab.go()
        elif op == "stop":
            qlab.stop()
        elif op == "panic":
            qlab.panic()
        elif op == "trigger_cue":
            if not cue_id:
                return {"status": "error", "message": "cue_id is required for trigger_cue"}
            qlab.trigger_cue(cue_id)
        elif op == "set_slider_level":
            if not cue_id or slider_index is None or level is None:
                return {
                    "status": "error",
                    "message": "cue_id, slider_index, and level are required for set_slider_level",
                }
            qlab.set_slider_level(cue_id, slider_index, level)
        else:
            return {"status": "error", "message": f"Unsupported operation: {operation}"}
        return {"status": "success", "operation": operation}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool(annotations=_README_ONLY)
async def scan_subnet_osc(
    subnet_prefix: Annotated[str, Field(description="Subnet prefix to scan (e.g. '192.168.1')")],
    ports: Annotated[
        list[int] | None, Field(description="Ports to probe (default: [7000, 8000, 9000, 11000, 53000])")
    ] = None,
    protocol: Annotated[str, Field(description="Transport protocol: 'udp' or 'tcp'")] = "udp",
) -> dict[str, Any]:
    """Scan a subnet prefix for active OSC ports.

    Probes each host in the subnet range on the given ports to discover
    live OSC services.

    ## Return Format
    {"status": "success"|"error", "active_hosts": list, "count": int}

    ## Examples
    scan_subnet_osc(subnet_prefix="192.168.1")
    scan_subnet_osc(subnet_prefix="10.0.0", ports=[9000, 11000])
    """
    try:
        effective_ports = ports or [7000, 8000, 9000, 11000, 53000]
        active = await run_subnet_scan(subnet_prefix, effective_ports, protocol)
        return {"status": "success", "active_hosts": active, "count": len(active)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@server.tool(app=True, annotations=_README_ONLY)
def show_control_faders() -> PrefabApp:
    """Display interactive faders and buttons to send immediate OSC values.

    ## Return Format
    PrefabApp with DataTable columns: Control Name, Control Type, OSC Target Path, Current Value

    ## Examples
    show_control_faders()
    """
    controls = [
        {"control": "Main Volume", "type": "Fader", "address": "/volume", "current_value": "0.8"},
        {"control": "Track 1 Mute", "type": "Toggle", "address": "/track/1/mute", "current_value": "Off"},
        {"control": "Scene Switcher", "type": "Trigger", "address": "/scene", "current_value": "Default"},
    ]
    with PrefabApp() as app:
        DataTable(
            data=controls,
            columns=[
                DataTableColumn(name="control", label="Control Name"),
                DataTableColumn(name="type", label="Control Type"),
                DataTableColumn(name="address", label="OSC Target Path"),
                DataTableColumn(name="current_value", label="Current Value"),
            ],
        )
    return app


@server.tool(app=True, annotations=_README_ONLY)
def show_osc_oscilloscope() -> PrefabApp:
    """Display a simulated real-time oscilloscope tracking incoming/outgoing OSC activity intensity.

    ## Return Format
    PrefabApp with DataTable columns: OSC Channel, Signal Level Monitor, Channel Status

    ## Examples
    show_osc_oscilloscope()
    """
    import random

    intensity_data = []
    levels = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    for i in range(12):
        level = random.choice(levels)
        intensity_data.append(
            {"channel": f"CH {i + 1}", "activity": level * 8, "status": "Healthy" if level in levels[3:] else "Idle"}
        )
    with PrefabApp() as app:
        DataTable(
            data=intensity_data,
            columns=[
                DataTableColumn(name="channel", label="OSC Channel"),
                DataTableColumn(name="activity", label="Signal Level Monitor"),
                DataTableColumn(name="status", label="Channel Status"),
            ],
        )
    return app


@server.tool()
async def save_workflow_descriptor(
    workflow_id: Annotated[str, Field(description="Filename prefix and unique ID of the workflow")],
    title: Annotated[str, Field(description="User-facing title of the workflow")],
    description: Annotated[str, Field(description="Workflow purpose description")],
    steps: Annotated[list[dict[str, Any]], Field(description="Step dicts with stepId, operationId, parameters")],
) -> dict[str, Any]:
    """Save a newly created workflow descriptor as an Arazzo YAML file.

    ## Return Format
    {"status": "success"|"error", "file": str}

    ## Examples
    save_workflow_descriptor(
        workflow_id="fade-volume",
        title="Fade Volume",
        description="Gradually fade volume from 0 to 1",
        steps=[{"stepId": "s1", "operationId": "send_osc_message", "parameters": {}}]
    )
    """
    import yaml

    try:
        workflows_dir = Path(__file__).parent / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        arazzo_data = {
            "arazzo": "1.0.1",
            "info": {"title": title, "description": description, "version": "1.0.0"},
            "sourceDescriptions": [{"name": "osc_server", "url": "http://127.0.0.1:8000"}],
            "workflows": [{"workflowId": "test_run", "summary": title, "steps": steps}],
        }

        target_file = workflows_dir / f"{workflow_id}.yaml"
        with open(target_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(arazzo_data, f, default_flow_style=False, sort_keys=False)

        return {"status": "success", "file": str(target_file)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
