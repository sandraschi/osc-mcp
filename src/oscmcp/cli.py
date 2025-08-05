""
Command-line interface for OSCMCP server.
"""
import asyncio
import logging
import os
import signal
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, server

logger = logging.getLogger(__name__)

app = FastAPI(
    title="OSCMCP",
    description="Open Source Content Management Platform MCP Server",
    version=__version__,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup."""
    await server.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await server.shutdown()

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}

# Add MCP protocol endpoints
@app.post("/mcp/execute")
async def execute_command(request: Request):
    """Execute an MCP command."""
    try:
        command = await request.json()
        logger.info(f"Received command: {command}")
        
        # TODO: Implement command execution logic
        result = {"status": "success", "result": "Command executed successfully"}
        
        return result
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return Response(
            content={"status": "error", "message": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    ""
    Run the OSCMCP server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
    
    server = uvicorn.Server(config)
    
    # Handle graceful shutdown
    async def shutdown(signal):
        logger.info(f"Received exit signal {signal}...")
        await server.shutdown()
        
    loop = asyncio.get_event_loop()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))
    
    # Run the server
    try:
        logger.info(f"Starting OSCMCP server on {host}:{port}")
        loop.run_until_complete(server.serve())
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        loop.close()
        logger.info("Server stopped")

def main():
    """Main entry point for the CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OSCMCP Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run the server
    run_server(host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
