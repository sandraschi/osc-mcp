"""Skills API — expose MCP skill preprompts over REST."""

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
    }
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
