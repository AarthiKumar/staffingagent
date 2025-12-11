"""Main FastAPI application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    # Startup
    setup_logging("INFO" if not settings.is_dev else "DEBUG")
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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Staffing Agent API", "version": "0.1.0"}
