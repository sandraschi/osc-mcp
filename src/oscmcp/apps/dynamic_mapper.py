"""Dynamic OSCQuery to MCP tool auto-mapper."""

import logging
from typing import Any

from fastmcp import FastMCP

from .oscquery import OSCQueryBrowser, OSCQueryService

logger = logging.getLogger(__name__)


class DynamicToolMapper:
    """Auto-discovers OSCQuery endpoints and registers them as MCP tools."""

    def __init__(self, server: FastMCP):
        self.server = server
        self.browser = OSCQueryBrowser()
        self.browser.on_service_change(self._handle_service_change)
        self.mapped_services: dict[str, OSCQueryService] = {}

    async def start(self) -> None:
        """Start the discovery browser."""
        logger.info("Starting Dynamic OSCQuery Tool Mapper...")
        await self.browser.start()

    async def stop(self) -> None:
        """Stop the discovery browser."""
        logger.info("Stopping Dynamic OSCQuery Tool Mapper...")
        await self.browser.stop()

    def get_services(self) -> list[dict[str, Any]]:
        """Returns details of all active discovered services."""
        services_list = []
        for service in self.mapped_services.values():
            services_list.append(
                {
                    "name": service.name,
                    "host": service.host,
                    "osc_port": service.osc_port,
                    "ws_port": service.ws_port,
                    "info": service.info,
                }
            )
        return services_list

    async def get_service_parameters(self, name: str) -> list[dict[str, Any]]:
        """Fetch all parameters for a specific service."""
        for service in self.mapped_services.values():
            if service.name.lower() == name.lower():
                return await service.list_parameters()
        return []

    def _handle_service_change(self, action: str, service: OSCQueryService) -> None:
        """Callback for zeroconf discovery updates."""
        if action == "added":
            self.mapped_services[service.name] = service
            logger.info(f"Discovered OSCQuery target: {service.name} ({service.host}:{service.osc_port})")
            self._register_service_tools(service)
        elif action == "removed":
            if service.name in self.mapped_services:
                del self.mapped_services[service.name]
            logger.info(f"OSCQuery target disconnected: {service.name}")
            self._unregister_service_tools(service)

    def _register_service_tools(self, service: OSCQueryService) -> None:
        """Register MCP tool wrapper for discovered targets."""
        tool_name = f"oscquery_{service.name.lower().replace('-', '_')}_set"

        async def dynamic_set_parameter(path: str, value: str) -> dict[str, Any]:
            """Dynamically sets a parameter on a discovered OSCQuery device.

            Args:
                path: Parameter address path (e.g. '/slider1', '/gain')
                value: String representation of value to send (cast automatically based on path)
            """
            # Find parameter type from the service tree
            parameters = await service.list_parameters()
            param_type = "s"  # default
            for p in parameters:
                if p["path"] == path:
                    param_type = p["type"]
                    break

            # Auto-cast based on OSCQuery type hint
            try:
                cast_val: Any = value
                if "f" in param_type:
                    cast_val = float(value)
                elif "i" in param_type:
                    cast_val = int(value)
                elif "T" in param_type:
                    cast_val = True
                elif "F" in param_type:
                    cast_val = False
                elif "N" in param_type:
                    cast_val = None

                service.send(path, [cast_val] if cast_val is not None else [])
                logger.info(f"OSCQuery Set: {service.name} {path} -> {cast_val}")
                return {
                    "status": "success",
                    "service": service.name,
                    "path": path,
                    "value": cast_val,
                    "type": param_type,
                }
            except Exception as e:
                err = f"Failed to set parameter: {e}"
                logger.error(err)
                return {"status": "error", "message": err}

        # Override name and docstring to display properly in MCP catalogs
        dynamic_set_parameter.__name__ = tool_name
        dynamic_set_parameter.__doc__ = (
            f"Control parameters for discovered target '{service.name}'.\nHost: {service.host}:{service.osc_port}"
        )

        # Register on FastMCP server
        try:
            self.server.add_tool(dynamic_set_parameter)
            logger.info(f"Registered dynamic MCP tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error registering tool {tool_name}: {e}")

    def _unregister_service_tools(self, service: OSCQueryService) -> None:
        """Unregister MCP tool from server."""
        tool_name = f"oscquery_{service.name.lower().replace('-', '_')}_set"
        try:
            if hasattr(self.server, "remove_tool"):
                self.server.remove_tool(tool_name)
            logger.info(f"Unregistered dynamic MCP tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error unregistering tool {tool_name}: {e}")
