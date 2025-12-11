"""Structured JSON logging"""
import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
agent_id_var: ContextVar[Optional[str]] = ContextVar("agent_id", default=None)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "agent_id": agent_id_var.get(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO"):
    """Configure structured logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None, agent_id: Optional[str] = None):
    """Set request context for logging"""
    if request_id:
        request_id_var.set(request_id)
    else:
        request_id_var.set(str(uuid.uuid4()))
    if user_id:
        user_id_var.set(user_id)
    if agent_id:
        agent_id_var.set(agent_id)
