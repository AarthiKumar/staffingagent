"""Main FastAPI application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import get_api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    # Startup
    setup_logging("INFO" if not settings.is_dev else "DEBUG")

    # Log Auth0 configuration status
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info(f"Auth0 Domain: {settings.auth0_domain or 'NOT SET'}")
    logger.info(f"Auth0 Audience: {settings.auth0_audience or 'NOT SET'}")
    logger.info(f"Auth0 Client ID: {settings.auth0_client_id or 'NOT SET'}")

    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Staffing Agent API",
    description="Internal staffing agent with optional LLM features",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(get_api_router(), prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Staffing Agent API", "version": "0.1.0"}
