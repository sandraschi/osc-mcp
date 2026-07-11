"""Fleet Management API for OSC-MCP.

Standardized endpoints for cross-app orchestration and launch protocols.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["fleet"], prefix="/v1/fleet")


class FleetLaunchRequest(BaseModel):
    """Request model for launching a fleet application."""

    repo_path: str = Field(..., description="Absolute path to the repository root")


class FleetLaunchResponse(BaseModel):
    """Response model for fleet launch operation."""

    success: bool
    message: str


@router.post("/launch", response_model=FleetLaunchResponse)
async def launch_app(request: FleetLaunchRequest) -> FleetLaunchResponse:
    """Launch another MCP app via its start.ps1 script.

    This implements the standardized SOTA fleet orchestration protocol.
    """
    path = Path(request.repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Path {request.repo_path} does not exist",
        )

    # Security check: Ensure path is within D:/Dev/repos
    try:
        allowed_base = Path("D:/Dev/repos").resolve()
        target_path = path.resolve()
        target_path.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Path outside allowed directory",
        )

    # Standardized SOTA entry point search
    # 1. web_sota/start.ps1
    # 2. web/start.ps1
    # 3. start.ps1 (root)

    start_script = path / "web_sota" / "start.ps1"
    if not start_script.exists():
        start_script = path / "web" / "start.ps1"
        if not start_script.exists():
            start_script = path / "start.ps1"
            if not start_script.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid SOTA entry point (start.ps1) found",
                )

    try:
        # Launch in a new terminal window
        subprocess.Popen(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(start_script),
            ],
            cwd=str(path),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        logger.info(f"Launched fleet application: {path.name} via {start_script}")
        return FleetLaunchResponse(success=True, message=f"Launched {path.name} successfully")
    except Exception as e:
        logger.error(f"Failed to launch {path.name}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Launch failed: {e!s}"
        )
