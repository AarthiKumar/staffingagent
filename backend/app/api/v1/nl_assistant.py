"""Natural language assistant endpoints"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.services.nl_filters import get_nl_filters_service

logger = get_logger(__name__)

router = APIRouter()


class NLParseRequest(BaseModel):
    agent_id: str
    text: str


class NLParseResponse(BaseModel):
    filters: Dict[str, Any]
    warnings: List[str]


@router.post("/parse", response_model=NLParseResponse)
def parse_nl_query(req: NLParseRequest, db: Session = Depends(get_db)):
    """Parse natural language into structured filters"""

    nl_service = get_nl_filters_service(req.agent_id)
    result = nl_service.parse(req.text)

    return NLParseResponse(
        filters=result.get("filters", {}),
        warnings=result.get("warnings", []),
    )
