#!/usr/bin/env python3
"""OSC to OBS WebSocket v5 Bridge.

This script runs a local bridge that listens for OSC messages on a UDP port (default: 7000)
and forwards them to OBS Studio's built-in WebSocket server (default: 4455).
This eliminates the need to install native C++ OSC plugins in OBS.
"""

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, Optional

import websockets
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("obs-bridge")

# Global queue for queueing OBS commands from OSC handlers
cmd_queue: asyncio.Queue = asyncio.Queue()


def get_uuid() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def make_request(request_type: str, request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format OBS WebSocket v5 Request payload."""
    payload = {
        "op": 6,
        "d": {
            "requestType": request_type,
            "requestId": get_uuid()
        }
    }
    if request_data is not None:
        payload["d"]["requestData"] = request_data
    return payload


def compute_auth_response(password: str, salt: str, challenge: str) -> str:
    """Generate OBS v5 WebSocket authentication response string."""
    # 1. Hash password + salt, then base64 encode
    secret_src = password + salt
    h1 = hashlib.sha256(secret_src.encode("utf-8")).digest()
    base64_secret = base64.b64encode(h1).decode("utf-8")

    # 2. Hash base64_secret + challenge, then base64 encode
    auth_src = base64_secret + challenge
    h2 = hashlib.sha256(auth_src.encode("utf-8")).digest()
    return base64.b64encode(h2).decode("utf-8")


# ── OSC Message Handlers ───────────────────────────────────────────────

def osc_handle_scene(address: str, *args: Any) -> None:
    """Handle /scene <scene_name> OSC message."""
    if not args or not isinstance(args[0], str):
        logger.warning("OSC /scene requires a string argument (scene_name)")
        return
    scene_name = args[0]
    logger.info(f"OSC -> Requesting scene switch: '{scene_name}'")
    req = make_request("SetCurrentProgramScene", {"sceneName": scene_name})
    cmd_queue.put_nowait(req)


def osc_handle_mute(address: str, *args: Any) -> None:
    """Handle /mute <source_name> OSC message."""
    if not args or not isinstance(args[0], str):
        logger.warning("OSC /mute requires a string argument (source_name)")
        return
    source_name = args[0]
    logger.info(f"OSC -> Requesting mute toggle: '{source_name}'")
    req = make_request("ToggleInputMute", {"inputName": source_name})
    cmd_queue.put_nowait(req)


def osc_handle_volume(address: str, *args: Any) -> None:
    """Handle /volume <source_name> <volume> OSC message."""
    if len(args) < 2 or not isinstance(args[0], str) or not isinstance(args[1], (int, float)):
        logger.warning("OSC /volume requires (string source_name, float volume)")
        return
    source_name = args[0]
    volume = float(args[1])
    # Clamp volume multiplier between 0.0 and 2.0 (OBS allows gain > 1.0)
    volume = max(0.0, min(volume, 2.0))
    logger.info(f"OSC -> Requesting volume level for '{source_name}' to {volume}")
    req = make_request("SetInputVolume", {"inputName": source_name, "inputVolumeMul": volume})
    cmd_queue.put_nowait(req)


def osc_handle_start_stream(address: str, *args: Any) -> None:
    """Handle /stream/start OSC message."""
    logger.info("OSC -> Requesting stream start")
    req = make_request("StartStream")
    cmd_queue.put_nowait(req)


def osc_handle_stop_stream(address: str, *args: Any) -> None:
    """Handle /stream/stop OSC message."""
    logger.info("OSC -> Requesting stream stop")
    req = make_request("StopStream")
    cmd_queue.put_nowait(req)


def osc_handle_custom_request(address: str, *args: Any) -> None:
    """Handle /obs/request <request_type> [json_string_data] OSC message."""
    if not args or not isinstance(args[0], str):
        logger.warning("OSC /obs/request requires a string argument (request_type)")
        return
    request_type = args[0]
    request_data = None
    if len(args) > 1 and isinstance(args[1], str):
        try:
            request_data = json.loads(args[1])
        except Exception as e:
            logger.warning(f"OSC /obs/request failed to parse JSON data: {e}")
            return

    logger.info(f"OSC -> Requesting custom operation: '{request_type}' with data: {request_data}")
    req = make_request(request_type, request_data)
    cmd_queue.put_nowait(req)


# ── Core WebSocket Client ──────────────────────────────────────────────

async def manage_websocket(uri: str, password: Optional[str]) -> None:
    """Connect to OBS WebSocket, handle authentication, and forward queued requests."""
    while True:
        try:
            logger.info(f"Connecting to OBS WebSocket at {uri}...")
            async with websockets.connect(uri) as ws:
                # 1. Wait for server Hello message (op: 0)
                hello_msg = await ws.recv()
                hello = json.loads(hello_msg)
                if hello.get("op") != 0:
                    logger.error(f"Unexpected initial message from OBS: {hello}")
                    await asyncio.sleep(5)
                    continue

                # 2. Perform authentication challenge if needed
                auth_req = hello["d"].get("authentication")
                identify_payload = {
                    "op": 1,
                    "d": {
                        "rpcVersion": 1,
                    }
                }

                if auth_req is not None:
                    if not password:
                        logger.error("OBS WebSocket requires password, but none was provided via --obs-password or OBS_WEBSOCKET_PASSWORD")
                        await ws.close()
                        await asyncio.sleep(5)
                        continue
                    
                    salt = auth_req["salt"]
                    challenge = auth_req["challenge"]
                    auth_resp = compute_auth_response(password, salt, challenge)
                    identify_payload["d"]["authentication"] = auth_resp

                # 3. Send Identify message (op: 1)
                await ws.send(json.dumps(identify_payload))

                # 4. Wait for Identified response (op: 2)
                identified_msg = await ws.recv()
                identified = json.loads(identified_msg)
                if identified.get("op") != 2:
                    logger.error(f"OBS authentication failed: {identified}")
                    await asyncio.sleep(5)
                    continue

                logger.info("Connected and authenticated with OBS WebSocket successfully!")

                # 5. Process queued commands and forward to WebSocket
                while True:
                    req = await cmd_queue.get()
                    try:
                        await ws.send(json.dumps(req))
                        logger.debug(f"Forwarded request to OBS: {req}")
                    except Exception as e:
                        logger.error(f"Failed to transmit request to OBS: {e}")
                        # Put back in queue to retry when connection is restored
                        cmd_queue.put_nowait(req)
                        raise e
                    finally:
                        cmd_queue.task_done()

        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            logger.warning(f"OBS WebSocket connection lost: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected WebSocket error: {e}. Retrying in 5 seconds...", exc_info=True)
            await asyncio.sleep(5)


# ── Main Entrypoint ────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="OSC-to-OBS WebSocket v5 Bridge")
    parser.add_argument("--host", default="127.0.0.1", help="OSC UDP server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7000, help="OSC UDP server port (default: 7000)")
    parser.add_argument("--obs-host", default="127.0.0.1", help="OBS WebSocket host (default: 127.0.0.1)")
    parser.add_argument("--obs-port", type=int, default=4455, help="OBS WebSocket port (default: 4455)")
    parser.add_argument("--obs-password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD"), help="OBS WebSocket password")
    args = parser.parse_args()

    # Set up OSC Dispatcher
    dispatcher = Dispatcher()
    dispatcher.map("/scene", osc_handle_scene)
    dispatcher.map("/mute", osc_handle_mute)
    dispatcher.map("/volume", osc_handle_volume)
    dispatcher.map("/stream/start", osc_handle_start_stream)
    dispatcher.map("/stream/stop", osc_handle_stop_stream)
    dispatcher.map("/obs/request", osc_handle_custom_request)

    # Start OSC Server
    loop = asyncio.get_running_loop()
    osc_server = AsyncIOOSCUDPServer((args.host, args.port), dispatcher, loop)
    transport, _ = await osc_server.create_serve_endpoint()
    logger.info(f"OSC UDP server listening on {args.host}:{args.port}")

    # Start WebSocket client manager
    ws_uri = f"ws://{args.obs_host}:{args.obs_port}"
    ws_task = asyncio.create_task(manage_websocket(ws_uri, args.obs_password))

    try:
        await ws_task
    except asyncio.CancelledError:
        logger.info("Bridge shutting down...")
    finally:
        transport.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process terminated by user.")
        sys.exit(0)
