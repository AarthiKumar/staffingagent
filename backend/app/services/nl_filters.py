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
        self._openai_client = None

        if self.enabled and settings.llm_provider == "openai":
            self._init_openai_client()

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        if not settings.llm_api_key:
            logger.warning("OpenAI API key not configured, NL assist will be disabled")
            self.enabled = False
            return

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(
                api_key=settings.llm_api_key,
                timeout=self.timeout_ms / 1000.0  # Convert to seconds
            )
            logger.info("OpenAI client initialized for NL filters")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.enabled = False

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
        provider = settings.llm_provider

        if provider == "disabled":
            raise ValueError("LLM provider disabled")

        if provider == "openai":
            return self._call_openai_parse(text)
        else:
            logger.warning(f"Unsupported LLM provider: {provider}, using fallback")
            return self._fallback_parse(text)

    def _call_openai_parse(self, text: str) -> Dict[str, Any]:
        """Call OpenAI API to parse natural language into structured filters"""
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # Build prompt for filter extraction
        prompt = self._build_filter_prompt(text)

        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective for parsing
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at parsing job requirements and candidate search queries. Extract structured filters from natural language text. Return ONLY a JSON object with the extracted filters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent parsing
            )

            # Parse response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            # Extract filters - expect {"filters": {...}, "warnings": [...]}
            if "filters" in result_json:
                return {
                    "filters": result_json["filters"],
                    "warnings": result_json.get("warnings", [])
                }
            else:
                logger.warning("OpenAI response missing 'filters' key")
                return {"filters": {}, "warnings": ["Invalid LLM response format"]}

        except Exception as e:
            logger.error(f"OpenAI parse call failed: {e}")
            raise

    def _build_filter_prompt(self, text: str) -> str:
        """Build prompt for filter extraction"""
        prompt = f"""Parse the following search query or job requirements into structured filters:

Query: "{text}"

Extract the following information if present:
1. **required_skills**: List of technical skills, technologies, or tools mentioned (e.g., ["python", "docker", "aws"])
2. **min_years**: Minimum years of experience per skill as a dictionary (e.g., {{"python": 5, "aws": 3}})
3. **location**: Geographic location or remote preference (e.g., "San Francisco" or "Remote")
4. **certifications**: Required certifications (e.g., ["AWS Certified", "PMP"])
5. **job_title**: Specific job titles or roles (e.g., "Senior Software Engineer")
6. **education**: Education requirements (e.g., "Bachelor's in Computer Science")

Return your response as a JSON object with this structure:
{{
  "filters": {{
    "required_skills": ["skill1", "skill2"],
    "min_years": {{"skill1": 3, "skill2": 5}},
    "location": "location string",
    "certifications": ["cert1"],
    "job_title": "title",
    "education": "education requirement"
  }},
  "warnings": ["any warnings about ambiguous or missing information"]
}}

IMPORTANT:
- Only include fields where you found relevant information
- Skills should be lowercase and standardized (e.g., "javascript" not "JavaScript" or "JS")
- Be conservative - only extract information you're confident about
- If years of experience are mentioned generally (e.g., "5+ years experience"), apply to all mentioned skills
- Return empty warnings array if no warnings

Your response:"""

        return prompt

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
