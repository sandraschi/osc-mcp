"""Onboarding status API for OSC-MCP.

Read-only install/process detection for the external host apps this server
wraps via OSC (see oscmcp.app_detect). Never launches anything.
"""

from fastapi import APIRouter

from oscmcp.app_detect import detect_all

router = APIRouter(tags=["onboarding"], prefix="/onboarding")


@router.get("/apps")
async def onboarding_apps() -> dict:
    """Install/running status for every app this server wraps via OSC.

    `testable_here` is false only for macOS-only apps (QLab) when running on
    a non-macOS host - it does not mean "don't bother", it means this
    specific machine structurally cannot run that app at all.
    """
    statuses = detect_all()
    return {
        "apps": [
            {
                "key": s.key,
                "display_name": s.display_name,
                "installed": s.installed,
                "installed_path": s.installed_path,
                "running": s.running,
                "process_pid": s.process_pid,
                "default_osc_port": s.default_osc_port,
                "license": s.license,
                "platform": s.platform,
                "download_url": s.download_url,
                "testable_here": s.testable_here,
                "notes": s.notes,
            }
            for s in statuses
        ],
        "installed_count": sum(1 for s in statuses if s.installed),
        "total_count": len(statuses),
    }
