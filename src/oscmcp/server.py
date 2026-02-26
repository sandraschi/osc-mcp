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

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient

from .sampling import osc_sampler

# Set up logging
logger = logging.getLogger(__name__)

# Create FastMCP instance with conversational capabilities
server = FastMCP("OSC-MCP")

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
async def send_osc_message(host: str, port: int, address: str, values: List[Any]) -> Dict[str, Any]:
    """Send OSC message to target application with conversational guidance.

    This tool sends OSC messages and provides intelligent follow-up suggestions
    for building complex automation workflows.

    Args:
        host: Target host IP address
        port: Target port number
        address: OSC address pattern (e.g., "/volume")
        values: List of values to send (will be converted to appropriate OSC types)

    Returns:
        Conversational response with status, suggestions, and next steps

    Example:
        await send_osc_message("127.0.0.1", 8000, "/volume", [0.8])
    """
    try:
        client = SimpleUDPClient(host, port)
        client.send_message(address, values)
        logger.info("Sent OSC message to %s:%s - %s: %s", host, port, address, values)

        # Validate the message using LLM sampling
        validation = await osc_sampler.validate_osc_message(address, values)

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
        # Here you can add custom message handling logic
        # For example, you could emit events or call other functions

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
        target_application: Target application name (optional, for better suggestions)
        host: Default target host
        port: Default target port

    Returns:
        Conversational response with generated workflow and implementation guidance

    Example:
        await generate_osc_workflow("Create a volume fade-out over 5 seconds", "Ableton Live")
    """
    try:
        # Use sampling to generate the workflow
        workflow = await osc_sampler.generate_osc_workflow(
            workflow_description, target_application, host, port
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
    workflow_data: Dict[str, Any], validate_first: bool = True
) -> Dict[str, Any]:
    """Execute a generated OSC workflow with intelligent validation.

    This tool runs complete OSC automation sequences with real-time
    validation and conversational feedback during execution.

    Args:
        workflow_data: Workflow dictionary from generate_osc_workflow
        validate_first: Whether to validate workflow before execution

    Returns:
        Conversational response with execution results and analysis

    Example:
        workflow = await generate_osc_workflow("Fade volume to 0 over 3 seconds")
        result = await execute_osc_workflow(workflow["workflow"])
    """
    try:
        # Validate workflow if requested
        if validate_first:
            validation = await osc_sampler.validate_osc_workflow(workflow_data)
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
async def test_osc_echo(port: int = 9000) -> Dict[str, Any]:
    """Test OSC functionality with conversational guidance and intelligent validation.

    This enhanced test function uses LLM sampling to validate OSC connectivity
    and provides detailed troubleshooting guidance.

    Args:
        port: Test port to use (default: 9000)

    Returns:
        Conversational response with test results and next steps
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

    send_result = await send_osc_message("127.0.0.1", port, test_address, test_values)
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
    test_analysis = await osc_sampler.analyze_osc_test(server_result, send_result)

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
