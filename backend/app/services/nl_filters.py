"""Natural language to filters service"""
import json
import time
from typing import Any, Dict, List

from app.core.config import AgentConfig, settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NLFiltersService:
    """Parse natural language into structured filters"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = AgentConfig(agent_id)
        self.enabled = self.config.get("llm.nl_assist.enabled", False)
        self.timeout_ms = 600

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into filters"""

        if not self.enabled or settings.llm_provider == "disabled":
            logger.info("NL assist disabled")
            return {"filters": {}, "warnings": ["NL assist is disabled"]}

        try:
            start_time = time.time()

            # Call LLM to extract filters
            filters = self._call_llm_parse(text)

            elapsed_ms = int((time.time() - start_time) * 1000)

            if elapsed_ms > self.timeout_ms:
                logger.warning(f"NL parse exceeded timeout: {elapsed_ms}ms")
                return {"filters": {}, "warnings": ["Request timed out"]}

            # Validate and normalize
            validated = self._validate_filters(filters)

            logger.info(f"NL parse completed in {elapsed_ms}ms")
            return validated

        except Exception as e:
            logger.error(f"NL parse failed: {e}")
            return {"filters": {}, "warnings": [f"Parse error: {str(e)}"]}

    def _call_llm_parse(self, text: str) -> Dict[str, Any]:
        """Call LLM to parse text into filters"""
        # This is a stub implementation
        # In production, call actual LLM API with constrained JSON output

        provider = settings.llm_provider

        if provider == "disabled":
            raise ValueError("LLM provider disabled")

        # TODO: Implement actual LLM API calls
        # For now, return basic keyword extraction
        logger.warning("LLM NL parse not implemented, using fallback")

        return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback keyword-based parsing"""
        import re

        filters = {}

        # Extract tech keywords as skills
        tech_keywords = re.findall(
            r"\b(?:python|java|javascript|typescript|react|node|docker|kubernetes|aws|azure|terraform|ansible|jenkins|go|rust)\b",
            text,
            re.IGNORECASE,
        )
        if tech_keywords:
            filters["required_skills"] = [k.lower() for k in set(tech_keywords)]

        # Extract experience years
        years_match = re.search(r"(\d+)\+?\s*years?", text, re.IGNORECASE)
        if years_match:
            years = int(years_match.group(1))
            filters["min_years"] = {skill: years for skill in filters.get("required_skills", [])}

        # Extract location
        location_match = re.search(r"\b(?:in|from|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
        if location_match:
            filters["location"] = location_match.group(1)

        return {"filters": filters, "warnings": ["Using fallback parser"]}

    def _validate_filters(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize filter structure"""
        filters = result.get("filters", {})
        warnings = result.get("warnings", [])

        # Ensure required_skills is a list
        if "required_skills" in filters and not isinstance(filters["required_skills"], list):
            filters["required_skills"] = []
            warnings.append("Invalid required_skills format")

        # Ensure min_years is a dict
        if "min_years" in filters and not isinstance(filters["min_years"], dict):
            filters["min_years"] = {}
            warnings.append("Invalid min_years format")

        return {"filters": filters, "warnings": warnings}


def get_nl_filters_service(agent_id: str) -> NLFiltersService:
    """Get NL filters service for agent"""
    return NLFiltersService(agent_id)
