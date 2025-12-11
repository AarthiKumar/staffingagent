"""Health check endpoints"""
from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.db.session import get_db
from app.telemetry.metrics import registry

router = APIRouter()


@router.get("/healthz")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    # Test database connection
    try:
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
