"""Reactive Trigger Engine to link incoming OSC messages to MCP tools."""

import fnmatch
import logging
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class ReactiveTriggerEngine:
    """Matches incoming OSC messages to tool execution actions."""

    def __init__(self, server: FastMCP | None = None):
        self.server = server
        self.triggers: list[dict[str, Any]] = []

    def set_server(self, server: FastMCP) -> None:
        self.server = server

    def register_trigger(self, address_pattern: str, target_tool: str, args_template: dict[str, Any]) -> None:
        """Register a new trigger action."""
        self.triggers.append({"pattern": address_pattern, "tool": target_tool, "template": args_template})
        logger.info(f"Registered reactive trigger: {address_pattern} -> {target_tool}")

    def get_triggers(self) -> list[dict[str, Any]]:
        """Returns all registered triggers."""
        return self.triggers

    def remove_trigger(self, pattern: str) -> None:
        """Remove trigger matching pattern."""
        self.triggers = [t for t in self.triggers if t["pattern"] != pattern]
        logger.info(f"Removed reactive trigger: {pattern}")

    def handle_message(self, address: str, args: tuple) -> None:
        """Checks incoming message against triggers and schedules executions."""
        for trigger in self.triggers:
            if fnmatch.fnmatch(address, trigger["pattern"]):
                logger.info(f"Reactive Trigger Fired! Address {address} matched pattern {trigger['pattern']}")
                if self.server:
                    # Resolve templates e.g. replacing "$0" with first argument, "$1" with second
                    resolved_args = {}
                    for k, v in trigger["template"].items():
                        resolved_val = v
                        if isinstance(v, str):
                            if v.startswith("$"):
                                try:
                                    idx = int(v[1:])
                                    if idx < len(args):
                                        resolved_val = args[idx]
                                except ValueError:
                                    if v == "$args" or v == "$value":
                                        resolved_val = list(args) if len(args) > 1 else (args[0] if args else None)
                        resolved_args[k] = resolved_val

                    # Call the tool asynchronously in the running event loop
                    import asyncio

                    asyncio.create_task(self._execute_tool(trigger["tool"], resolved_args))

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Asynchronously call target tool."""
        try:
            logger.info(f"Executing target tool: {tool_name} with arguments: {arguments}")
            # FastMCP call_tool is async
            result = await self.server.call_tool(tool_name, arguments)
            logger.info(f"Reactive execution of {tool_name} finished: {result}")
        except Exception as e:
            logger.error(f"Error executing dynamic reactive tool {tool_name}: {e}")


# Global instance of reactive engine
global_trigger_engine = ReactiveTriggerEngine()
