"""Main entry point for OSC-MCP FastAPI server."""

import logging
import platform
import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oscmcp.api import api_router
from oscmcp.server import server as mcp_server

logger = logging.getLogger(__name__)

_START_TIME = time.time()

app = FastAPI(title="OSC-MCP API", description="REST interface for OSC-MCP tools", version="0.3.0")

# Enable CORS for the webapp and Tauri WebView
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10766",
        "http://127.0.0.1:10766",
        "http://localhost:10767",
        "http://127.0.0.1:10767",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/v1/health")
@app.get("/health")
async def health():
    return {"status": "ok", "server": "osc-mcp-sota", "version": "2026.2.17"}


@app.get("/api/v1/stats")
async def stats():
    return {
        "targets": {
            "ableton": {"status": "unknown", "port": 11000},
            "touchdesigner": {"status": "unknown", "port": 12000},
            "vrchat": {"status": "unknown", "port": 9000},
            "maxmsp": {"status": "unknown", "port": 13000},
            "supercollider": {"status": "unknown", "port": 57120},
            "vcvrack": {"status": "unknown", "port": 14000},
        },
        "messages_sent": 0,
        "uptime_seconds": 0,
        "backend_port": 10767,
    }


@app.get("/api/v1/diagnostics")
async def diagnostics():
    """Return server diagnostics: tool count, version, system info."""
    tool_count = 0
    if hasattr(mcp_server, "_tool_manager") and hasattr(mcp_server._tool_manager, "tools"):
        tool_count = len(mcp_server._tool_manager.tools)
    elif hasattr(mcp_server, "_tools"):
        tool_count = len(mcp_server._tools)

    return {
        "status": "ok",
        "server": "osc-mcp-sota",
        "version": "2026.2.17",
        "uptime_seconds": int(time.time() - _START_TIME),
        "tool_count": tool_count,
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "errors": [],
    }


@app.get("/api/v1/capabilities")
async def capabilities():
    """Return server capabilities for SOTA discovery."""
    from oscmcp.server import server as mcp_srv

    tool_count = 0
    if hasattr(mcp_srv, "_tool_manager") and hasattr(mcp_srv._tool_manager, "tools"):
        tool_count = len(mcp_srv._tool_manager.tools)
    return {
        "server": "OSC-MCP",
        "version": "0.3.2",
        "transport": ["stdio", "http"],
        "port": 10767,
        "features": ["tools", "resources", "prompts", "sampling", "prefab", "skills"],
        "tool_count": tool_count,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10767)
