"""OSCQuery integration for OSC-MCP.

This module provides OSCQuery protocol support for device discovery and
auto-configuration of OSC endpoints.
"""

import asyncio
import logging
import socket
import uuid
from typing import Dict, List, Optional, Callable, Any

import aiohttp
from zeroconf import ServiceInfo, Zeroconf, IPVersion
from zeroconf.asyncio import AsyncZeroconf

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class OSCQueryService:
    """Represents a discovered OSCQuery service."""

    def __init__(
        self,
        name: str,
        host: str,
        osc_port: int,
        ws_port: Optional[int] = None,
        info: Optional[Dict] = None,
    ):
        self.name = name
        self.host = host
        self.osc_port = osc_port
        self.ws_port = ws_port
        self.info = info or {}
        self.osc_client = OSCClient(host, osc_port)

    def __str__(self) -> str:
        return f"OSCQueryService(name='{self.name}', host='{self.host}', osc_port={self.osc_port}, ws_port={self.ws_port})"

    def __repr__(self) -> str:
        return self.__str__()

    async def get_host_info(self) -> Dict:
        """Get the host info from the OSCQuery service."""
        if not hasattr(self, "_host_info"):
            await self._fetch_host_info()
        return self._host_info

    async def _fetch_host_info(self) -> None:
        """Fetch the host info from the OSCQuery service."""
        url = f"http://{self.host}:{self.ws_port}/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        self._host_info = await response.json()
                    else:
                        self._host_info = {}
                        logger.warning(f"Failed to fetch host info: {response.status}")
        except Exception as e:
            self._host_info = {}
            logger.error(f"Error fetching host info: {e}")

    async def query(self, path: str = "") -> Dict:
        """Query the OSCQuery service for information about an OSC address.

        Args:
            path: OSC address path to query (e.g., "/parameter1")

        Returns:
            Dictionary containing the query response
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"http://{self.host}:{self.ws_port}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to query {path}: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error querying {path}: {e}")
            return {}

    async def list_parameters(self) -> List[Dict]:
        """List all available OSC parameters from the service."""
        host_info = await self.get_host_info()
        parameters = []

        def traverse(node: Dict, path: str = "") -> None:
            current_path = path + node.get("FULL_PATH", node.get("NAME", ""))

            # If this node has a TYPE, it's a parameter
            if "TYPE" in node:
                parameters.append(
                    {
                        "path": current_path,
                        "type": node["TYPE"],
                        "description": node.get("DESCRIPTION", ""),
                        "access": node.get("ACCESS", 0),
                        "value": node.get("VALUE"),
                        "range": node.get("RANGE"),
                        "tags": node.get("TAGS", []),
                    }
                )

            # Recursively process children
            for child in node.get("CONTENTS", {}).values():
                traverse(child, current_path + "/")

        if "CONTENTS" in host_info:
            for node in host_info["CONTENTS"].values():
                traverse(node)

        return parameters

    def send(self, address: str, *args) -> None:
        """Send an OSC message to this service.

        Args:
            address: OSC address to send to
            *args: Arguments to send
        """
        self.osc_client.send(address, *args)
        logger.debug(f"Sent to {self.name}: {address} {args}")


class OSCQueryBrowser:
    """Browser for discovering OSCQuery services on the network."""

    SERVICE_TYPE = "_oscjson._tcp.local."

    def __init__(self):
        self.zeroconf = None
        self.services = {}
        self._service_listeners = []
        self._browser = None

    async def start(self) -> None:
        """Start browsing for OSCQuery services."""
        if self.zeroconf is not None:
            return

        self.zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
        self._browser = await self.zeroconf.zeroconf.async_add_listener(
            self._service_state_change, self.SERVICE_TYPE
        )
        logger.info("OSCQuery browser started")

    async def stop(self) -> None:
        """Stop browsing for OSCQuery services."""
        if self.zeroconf is not None:
            if self._browser is not None:
                await self.zeroconf.zeroconf.async_remove_listener(self._browser)
                self._browser = None
            await self.zeroconf.async_close()
            self.zeroconf = None
            logger.info("OSCQuery browser stopped")

    def _service_state_change(
        self, zeroconf: Zeroconf, service_type: str, name: str, state_change: str
    ) -> None:
        """Handle service state changes."""
        if state_change == "add":
            asyncio.create_task(self._add_service(zeroconf, service_type, name))
        elif state_change == "remove":
            self._remove_service(name)

    async def _add_service(
        self, zeroconf: Zeroconf, service_type: str, name: str
    ) -> None:
        """Add a discovered OSCQuery service."""
        try:
            info = await zeroconf.async_get_service_info(service_type, name)
            if info:
                host = info.parsed_addresses()[0]
                port = info.port
                props = {}

                # Parse TXT record
                for key, value in info.properties.items():
                    try:
                        if isinstance(key, bytes):
                            key = key.decode("utf-8")
                        if isinstance(value, bytes):
                            value = value.decode("utf-8")
                        props[key] = value
                    except Exception as e:
                        logger.warning(f"Error parsing property {key}: {e}")

                # Get OSC port from TXT record or use default
                osc_port = int(props.get("osc.port", 0))
                if osc_port == 0:
                    # If no OSC port specified, try to get it from the service name
                    # (some implementations include it in the name like "ServiceName.osc._oscjson._tcp.local.")
                    for part in name.split("."):
                        if part.isdigit() and len(part) >= 4:  # Likely a port number
                            osc_port = int(part)
                            break

                    if osc_port == 0:
                        # Default OSC port if not specified
                        osc_port = 8000

                # Create service object
                service = OSCQueryService(
                    name=name.split(".")[0],
                    host=host,
                    osc_port=osc_port,
                    ws_port=port,
                    info=props,
                )

                # Store service
                self.services[name] = service
                logger.info(f"Discovered OSCQuery service: {service}")

                # Notify listeners
                for callback in self._service_listeners:
                    try:
                        callback("added", service)
                    except Exception as e:
                        logger.error(f"Error in service listener: {e}")

        except Exception as e:
            logger.error(f"Error adding service {name}: {e}")

    def _remove_service(self, name: str) -> None:
        """Remove a service that is no longer available."""
        if name in self.services:
            service = self.services.pop(name)
            logger.info(f"OSCQuery service removed: {service}")

            # Notify listeners
            for callback in self._service_listeners:
                try:
                    callback("removed", service)
                except Exception as e:
                    logger.error(f"Error in service listener: {e}")

    def on_service_change(
        self, callback: Callable[[str, OSCQueryService], None]
    ) -> None:
        """Register a callback for service changes.

        Args:
            callback: Function that takes (action, service) where action is 'added' or 'removed'
                     and service is an OSCQueryService instance
        """
        self._service_listeners.append(callback)

    def get_services(self) -> List[OSCQueryService]:
        """Get a list of all discovered services."""
        return list(self.services.values())

    def find_service(self, name: str) -> Optional[OSCQueryService]:
        """Find a service by name.

        Args:
            name: Service name to find (case-insensitive partial match)

        Returns:
            OSCQueryService if found, None otherwise
        """
        name = name.lower()
        for service in self.services.values():
            if name in service.name.lower():
                return service
        return None


class OSCQueryServer:
    """OSCQuery server implementation for OSC-MCP.

    This class implements the OSCQuery protocol to expose OSC endpoints
    for discovery and querying by OSCQuery clients.
    """

    def __init__(
        self,
        name: str = "OSC-MCP",
        osc_port: int = 8000,
        http_port: int = 8001,
        host: str = "0.0.0.0",
    ):
        """Initialize the OSCQuery server.

        Args:
            name: Service name for discovery
            osc_port: Port for OSC communication
            http_port: Port for HTTP/WebSocket (OSCQuery) communication
            host: Host address to bind to
        """
        self.name = name
        self.osc_port = osc_port
        self.http_port = http_port
        self.host = host

        # OSC server
        self.osc_server = OSCServer(host, osc_port)

        # HTTP server
        self.app = None
        self.runner = None
        self.site = None

        # Service info for Zeroconf
        self.zeroconf = None
        self.service_info = None

        # Endpoint registry
        self.endpoints = {}

        # Generate a unique ID for this server
        self.server_id = str(uuid.uuid4())

    def add_endpoint(
        self,
        path: str,
        type_hint: str = None,
        description: str = "",
        access: int = 3,  # Read/Write by default
        value: Any = None,
        range_min: float = None,
        range_max: float = None,
        tags: List[str] = None,
    ) -> None:
        """Add an OSC endpoint to the OSCQuery server.

        Args:
            path: OSC address path (e.g., "/parameter1")
            type_hint: Type hint (e.g., "f" for float, "i" for int, "s" for string)
            description: Human-readable description of the parameter
            access: Access level (1=read-only, 2=write-only, 3=read/write)
            value: Current value of the parameter
            range_min: Minimum value (for numeric parameters)
            range_max: Maximum value (for numeric parameters)
            tags: Optional list of tags for categorization
        """
        if not path.startswith("/"):
            path = "/" + path

        # Create endpoint info
        endpoint = {
            "FULL_PATH": path,
            "ACCESS": access,
            "DESCRIPTION": description,
            "CONTENTS": {},
        }

        if type_hint is not None:
            endpoint["TYPE"] = type_hint

        if value is not None:
            endpoint["VALUE"] = value

        if range_min is not None and range_max is not None:
            endpoint["RANGE"] = {"MIN": range_min, "MAX": range_max}

        if tags:
            endpoint["TAGS"] = tags

        # Add to registry
        self.endpoints[path] = endpoint

    def remove_endpoint(self, path: str) -> None:
        """Remove an OSC endpoint.

        Args:
            path: OSC address path to remove
        """
        if path in self.endpoints:
            del self.endpoints[path]

    def update_endpoint_value(self, path: str, value: Any) -> None:
        """Update the current value of an endpoint.

        Args:
            path: OSC address path
            value: New value
        """
        if path in self.endpoints:
            self.endpoints[path]["VALUE"] = value

    async def start(self) -> None:
        """Start the OSCQuery server."""
        # Start OSC server
        await self.osc_server.start()

        # Start HTTP server
        await self._start_http_server()

        # Advertise service via Zeroconf
        await self._start_zeroconf()

        logger.info(f"OSCQuery server started at http://{self.host}:{self.http_port}")

    async def stop(self) -> None:
        """Stop the OSCQuery server."""
        # Stop Zeroconf
        await self._stop_zeroconf()

        # Stop HTTP server
        await self._stop_http_server()

        # Stop OSC server
        await self.osc_server.stop()

        logger.info("OSCQuery server stopped")

    async def _start_http_server(self) -> None:
        """Start the HTTP server for OSCQuery."""
        from aiohttp import web

        app = web.Application()

        # Root endpoint - returns host info
        async def handle_root(request):
            host_info = self._get_host_info()
            return web.json_response(host_info)

        # Parameter query endpoint
        async def handle_parameter(request):
            path = "/" + request.match_info.get("path", "")
            if path in self.endpoints:
                return web.json_response(self.endpoints[path])
            else:
                return web.HTTPNotFound()

        # Add routes
        app.router.add_get("/", handle_root)
        app.router.add_get("/{path:.*}", handle_parameter)

        # Start server
        self.runner = web.AppRunner(app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.http_port)
        await self.site.start()

        self.app = app

    async def _stop_http_server(self) -> None:
        """Stop the HTTP server."""
        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.app = None

    async def _start_zeroconf(self) -> None:
        """Start advertising the service via Zeroconf."""
        self.zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)

        # Create service info
        server_name = f"{socket.gethostname()}.local."

        props = {
            "txtvers": "1",
            "data": "json",
            "name": self.name,
            "osc.ip": self.host,
            "osc.port": str(self.osc_port),
            "osc.transport": "udp",
            "osc.stage": "dev",
            "server_id": self.server_id,
        }

        self.service_info = ServiceInfo(
            "_oscjson._tcp.local.",
            f"{self.name}._oscjson._tcp.local.",
            addresses=[socket.inet_aton(self.host)],
            port=self.http_port,
            properties=props,
            server=server_name,
        )

        # Register service
        await self.zeroconf.async_register_service(self.service_info)

    async def _stop_zeroconf(self) -> None:
        """Stop advertising the service."""
        if self.zeroconf and self.service_info:
            await self.zeroconf.async_unregister_service(self.service_info)
            self.service_info = None

        if self.zeroconf:
            await self.zeroconf.async_close()
            self.zeroconf = None

    def _get_host_info(self) -> Dict:
        """Get the host info document."""
        # Create the host info structure
        host_info = {
            "NAME": self.name,
            "OSC_IP": self.host,
            "OSC_PORT": self.osc_port,
            "OSC_TRANSPORT": "UDP",
            "EXTENSIONS": {
                "ACCESS": True,
                "VALUE": True,
                "RANGE": True,
                "TYPE": True,
                "DESCRIPTION": True,
                "TAGS": True,
                "CRITICAL": False,
                "CLIPMODE": False,
                "UNIT": False,
                "LISTEN": False,
                "PATHCHANGED": False,
                "RANGE_FREEDOM": False,
            },
            "CONTENTS": {},
        }

        # Add all endpoints to the contents
        for path, endpoint in sorted(self.endpoints.items()):
            parts = [p for p in path.split("/") if p]
            current = host_info["CONTENTS"]

            for i, part in enumerate(parts):
                is_leaf = i == len(parts) - 1

                if part not in current:
                    if is_leaf:
                        # Add the full endpoint
                        current[part] = endpoint
                    else:
                        # Add a container node
                        current[part] = {
                            "FULL_PATH": "/" + "/".join(parts[: i + 1]),
                            "CONTENTS": {},
                        }

                # Move to the next level
                if not is_leaf:
                    current = current[part]["CONTENTS"]

        return host_info


# Example usage
async def example_usage():
    """Example of using the OSCQueryServer class."""
    import asyncio

    # Create OSCQuery server
    server = OSCQueryServer(name="OSC-MCP-Server")

    # Add some endpoints
    server.add_endpoint(
        "/test/float",
        type_hint="f",
        description="A test float parameter",
        value=0.5,
        range_min=0.0,
        range_max=1.0,
        tags=["test", "float"],
    )

    server.add_endpoint(
        "/test/int",
        type_hint="i",
        description="A test integer parameter",
        value=42,
        range_min=0,
        range_max=100,
        tags=["test", "int"],
    )

    server.add_endpoint(
        "/test/string",
        type_hint="s",
        description="A test string parameter",
        value="hello",
        tags=["test", "string"],
    )

    # Start the server
    await server.start()

    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)

            # Update a value
            import random

            server.update_endpoint_value("/test/float", random.random())

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await server.stop()


async def example_browser():
    """Example of using the OSCQueryBrowser class."""
    import asyncio

    # Create browser
    browser = OSCQueryBrowser()

    # Define callback for service changes
    def on_service_change(action, service):
        print(f"Service {action}: {service}")

    # Register callback
    browser.on_service_change(on_service_change)

    # Start browsing
    await browser.start()

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await browser.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        asyncio.run(example_usage())
    else:
        asyncio.run(example_browser())
