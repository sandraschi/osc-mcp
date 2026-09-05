from fastapi import APIRouter

from oscmcp.api.v1.endpoints import fleet, llm, onboarding, patchstorage, skills, tools, vcv_library

api_router = APIRouter()
api_router.include_router(tools.router)
api_router.include_router(fleet.router)
api_router.include_router(skills.router)
api_router.include_router(llm.router)
api_router.include_router(onboarding.router)
api_router.include_router(vcv_library.router)
api_router.include_router(patchstorage.router)
