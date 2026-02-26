"""Main entry point for OSC-MCP FastAPI server."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oscmcp.api import api_router

app = FastAPI(title="OSC-MCP API", description="REST interface for OSC-MCP tools", version="0.3.0")

# Enable CORS for the webapp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual webapp origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/v1/health")
@app.get("/health")
async def health():
    return {"status": "ok", "server": "osc-mcp-sota", "version": "2026.2.17"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10767)
