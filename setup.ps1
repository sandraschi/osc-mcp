# OSCMCP Setup Script
# FastMCP 2.10 compliant OSC MCP implementation

# Create necessary directories
$directories = @(
    "src",
    "tests",
    "docs",
    "scripts",
    "config"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path ".\$dir" | Out-Null
}

# Create basic files
$files = @{
    "README.md" = @"
# OSCMCP - Open Sound Control MCP

FastMCP 2.10 compliant implementation of Open Sound Control protocol for cross-application communication.

## Features
- Send and receive OSC messages
- Support for common OSC patterns
- Built-in OSC message routing
- Integration with other MCPs
- DXT support for natural language control

## Quick Start

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Start the MCP server:
   ```powershell
   .\run.ps1
   ```

## DXT Examples
- "Send /test 1 2 3 to 192.168.1.100:8000"
- "Listen for /volume messages on port 9000"
- "Route /audio/* to AudioMCP"
- "Convert MIDI to OSC on channel 1"
"@

    "requirements.txt" = @"
python-osc>=1.8.1
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
python-dotenv>=0.19.0
"@

    "src\main.py" = @"
"""OSCMCP Main Module"""
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pythonosc import dispatcher, osc_server
from pythonosc.udp_client import SimpleUDPClient
from typing import Dict, List, Optional
import uvicorn
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oscmcp")

app = FastAPI(title="OSCMCP", version="1.0.0")

# OSC Clients and Servers
osc_clients: Dict[str, SimpleUDPClient] = {}
osc_servers: List[asyncio.Server] = []

class OSCMessage(BaseModel):
    address: str
    values: list

@app.on_event("startup")
async def startup_event():
    """Initialize OSC components"""
    logger.info("Starting OSCMCP...")
    # Add any initialization code here

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up OSC components"""
    logger.info("Shutting down OSCMCP...")
    for server in osc_servers:
        server.close()
    osc_servers.clear()

@app.post("/api/send")
async def send_osc(message: OSCMessage, host: str = "127.0.0.1", port: int = 8000):
    """Send an OSC message"""
    try:
        client = SimpleUDPClient(host, port)
        client.send_message(message.address, message.values)
        return {"status": "success", "message": f"Sent {message.address} to {host}:{port}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"@

    "run.ps1" = @"
# Run script for OSCMCP
$env:PYTHONUNBUFFERED=1
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"@
}

foreach ($file in $files.GetEnumerator()) {
    Set-Content -Path $file.Name -Value $file.Value -Encoding UTF8
}

Write-Host "OSCMCP project created successfully!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. cd d:\Dev\repos\oscmcp"
Write-Host "2. .\setup.ps1"
Write-Host "3. .\run.ps1"
