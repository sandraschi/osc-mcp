"""Skills API - expose MCP skill preprompts over REST."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["skills"], prefix="/skills")

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "skills"

_SKILLS_MANIFEST = {
    "osc-mcp-expert": {
        "name": "osc-mcp-expert",
        "title": "OSC-MCP Expert",
        "description": "Comprehensive skill covering all OSC tool capabilities, best practices, and configuration.",
    },
    "ableton-expert": {
        "name": "ableton-expert",
        "title": "Ableton Live Expert",
        "description": "AbletonOSC's real address space, ableton_manager's operations, and setup pitfalls.",
    },
    "vcvrack-expert": {
        "name": "vcvrack-expert",
        "title": "VCV Rack Expert",
        "description": "OSCelot's real slot-addressed protocol, vcv_manager's operations, and the separate patch-builder feature.",
    },
    "touchdesigner-expert": {
        "name": "touchdesigner-expert",
        "title": "TouchDesigner Expert",
        "description": "OSC In/Out CHOP and DAT conventions, and touchdesigner_manager's operations.",
    },
    "vrchat-expert": {
        "name": "vrchat-expert",
        "title": "VRChat Expert",
        "description": "VRChat's real OSC protocol (avatar parameters, input, chatbox, trackers) and vrchat_manager's operations.",
    },
    "supercollider-expert": {
        "name": "supercollider-expert",
        "title": "SuperCollider Expert",
        "description": "scsynth's real Server Command Reference and supercollider_manager's operations.",
    },
    "maxmsp-expert": {
        "name": "maxmsp-expert",
        "title": "Max/MSP Expert",
        "description": "Why Max has no fixed OSC namespace, real udpreceive/udpsend/odot objects, and maxmsp_manager's operations.",
    },
    "resolume-expert": {
        "name": "resolume-expert",
        "title": "Resolume Expert",
        "description": "Resolume's real shipped OSC address list and resolume_manager's operations.",
    },
    "qlab-expert": {
        "name": "qlab-expert",
        "title": "QLab Expert",
        "description": "Figure 53's real OSC Dictionary and qlab_manager's operations (macOS-only).",
    },
    "puredata-expert": {
        "name": "puredata-expert",
        "title": "Pure Data Expert",
        "description": "Why vanilla Pd has no OSC support, the mrpeach library, and puredata_manager's operations.",
    },
    "obs-expert": {
        "name": "obs-expert",
        "title": "OBS Studio Expert",
        "description": "The OSC-to-obs-websocket bridge architecture and obs_manager's operations.",
    },
}


def _read_skill_file(name: str) -> str:
    skill_dir = SKILLS_DIR / name
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        return skill_file.read_text(encoding="utf-8")
    return f"# {name}\n\nSkill content not found."


@router.get("/")
async def list_skills():
    """List all available preprompt skills."""
    return {"skills": list(_SKILLS_MANIFEST.values()), "count": len(_SKILLS_MANIFEST)}


@router.get("/{name}")
async def get_skill(name: str):
    """Return the full SKILL.md content for a named skill."""
    if name not in _SKILLS_MANIFEST:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{name}' not found")
    content = _read_skill_file(name)
    return {"name": name, "content": content}
