from fastapi import APIRouter

from oscmcp.api.v1.endpoints import fleet, llm, skills, tools

api_router = APIRouter()
api_router.include_router(tools.router)
api_router.include_router(fleet.router)
api_router.include_router(skills.router)
api_router.include_router(llm.router)
