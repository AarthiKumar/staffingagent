"""Cost tracking and budget management service"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import AgentConfig
from app.core.logging import get_logger
from app.models import LLMEvent

logger = get_logger(__name__)


class CostsService:
    """Track LLM costs and enforce budgets"""

    def __init__(self, db: Session, agent_id: str):
        self.db = db
        self.agent_id = agent_id
        self.config = AgentConfig(agent_id)
        self.monthly_budget = self.config.get("budgets.monthly_usd", 150.0)

    def get_current_month_spend(self) -> Decimal:
        """Get total spend for current month"""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        result = self.db.execute(
            select(func.sum(LLMEvent.cost_usd))
            .where(LLMEvent.agent_id == self.agent_id)
            .where(LLMEvent.ts >= month_start)
        ).scalar()

        return result or Decimal("0.0")

    def check_budget(self) -> Dict[str, any]:
        """Check if budget is exceeded"""
        current_spend = float(self.get_current_month_spend())
        budget = float(self.monthly_budget)
        remaining = budget - current_spend
        exceeded = remaining < 0

        return {
            "current_spend": current_spend,
            "monthly_budget": budget,
            "remaining": remaining,
            "exceeded": exceeded,
            "percentage": (current_spend / budget * 100) if budget > 0 else 0,
        }

    def should_disable_llm(self) -> bool:
        """Check if LLM features should be disabled due to budget"""
        budget_status = self.check_budget()
        if budget_status["exceeded"]:
            logger.warning(
                f"Budget exceeded for agent {self.agent_id}: "
                f"${budget_status['current_spend']:.2f} / ${budget_status['monthly_budget']:.2f}"
            )
            return True
        return False

    def log_llm_event(
        self,
        feature: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: Decimal,
        latency_ms: int,
        success: bool = True,
        cache_hit: bool = False,
        input_hash: str = None,
    ):
        """Log an LLM API call event"""
        event = LLMEvent(
            agent_id=self.agent_id,
            feature=feature,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            success=success,
            cache_hit=cache_hit,
            input_hash=input_hash,
        )
        self.db.add(event)
        self.db.commit()

        logger.info(
            f"LLM event logged: feature={feature} tokens={tokens_in}+{tokens_out} "
            f"cost=${cost_usd} latency={latency_ms}ms"
        )

    def estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> Decimal:
        """Estimate cost based on token counts"""
        # Simplified cost estimation (adjust for actual pricing)
        # Example: GPT-4 pricing ~$0.03/1K input, $0.06/1K output
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }

        model_key = next((k for k in pricing if k in model.lower()), "gpt-3.5-turbo")
        rates = pricing[model_key]

        cost = (tokens_in / 1000.0 * rates["input"]) + (tokens_out / 1000.0 * rates["output"])
        return Decimal(str(round(cost, 6)))


def get_costs_service(db: Session, agent_id: str) -> CostsService:
    """Get costs service for agent"""
    return CostsService(db, agent_id)
