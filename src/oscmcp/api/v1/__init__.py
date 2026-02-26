from fastapi import APIRouter

from oscmcp.api.v1.endpoints import tools, fleet

api_router = APIRouter()
api_router.include_router(tools.router)
api_router.include_router(fleet.router)
