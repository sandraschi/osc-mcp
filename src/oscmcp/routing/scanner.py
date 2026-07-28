"""Active subnet scanner for OSC listeners."""

import asyncio
import logging
import socket
from typing import Any

logger = logging.getLogger(__name__)


async def check_port(host: str, port: int, protocol: str = "udp", timeout: float = 0.2) -> bool:
    """Check if a specific port is active on a host."""
    if protocol == "tcp":
        try:
            _reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return True
        except Exception:
            return False
    else:
        # UDP Port check
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            # Send standard OSC dummy packet
            sock.sendto(b"/ping\x00\x00\x00,\x00\x00\x00", (host, port))
            # Test if it throws immediate ConnectionRefusedError (ICMP Port Unreachable)
            try:
                sock.recvfrom(1)
                return True
            except TimeoutError:
                # No ICMP refused received within timeout, likely listening or filtered
                return True
            except ConnectionRefusedError:
                return False
            except Exception:
                return True  # Fallback to true if other socket errors occur
        except Exception:
            return False


async def scan_subnet_osc(subnet_prefix: str, ports: list[int], protocol: str = "udp") -> list[dict[str, Any]]:
    """Scan a subnet prefix (e.g. '192.168.1') for active OSC ports."""
    tasks = []
    # Scan standard host range (1-254)
    for i in range(1, 255):
        host = f"{subnet_prefix}.{i}"
        for port in ports:
            tasks.append((host, port))

    active_hosts = []
    sem = asyncio.Semaphore(100)  # Concurrency lock

    async def worker(host: str, port: int):
        async with sem:
            if await check_port(host, port, protocol):
                active_hosts.append({"host": host, "port": port, "protocol": protocol, "status": "active"})

    await asyncio.gather(*(worker(h, p) for h, p in tasks))
    return active_hosts
