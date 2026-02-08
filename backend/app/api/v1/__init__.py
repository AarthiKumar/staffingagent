"""API v1 routes"""
from fastapi import APIRouter

from . import auth, availability, candidates, health, ingest, nl_assistant, search, sections, upload_async, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(upload_async.router, prefix="/async", tags=["async_upload"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(nl_assistant.router, prefix="/nl", tags=["nl_assistant"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
