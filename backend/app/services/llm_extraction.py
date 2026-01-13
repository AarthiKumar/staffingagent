"""LLM-based CV extraction service for consistent data extraction"""
import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMExtractionService:
    """Extract structured data from CVs using LLM"""

    def __init__(self):
        self.enabled = settings.llm_provider == "openai" and settings.llm_api_key
        self._openai_client = None

        if self.enabled:
            self._init_openai_client()

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        if not settings.llm_api_key:
            logger.warning("OpenAI API key not configured, LLM extraction will be disabled")
            self.enabled = False
            return

        try:
            from openai import OpenAI
            self._openai_client = OpenAI(
                api_key=settings.llm_api_key,
                timeout=30.0  # 30 second timeout for extraction
            )
            logger.info("OpenAI client initialized for CV extraction")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.enabled = False

    def extract_cv_data(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract structured data from CV text using LLM.

        Returns dict with:
        - name: str
        - email: str or None
        - location: str or None
        - summary: str
        - skills: List[str] - keywords only
        - experience: List[dict] - with org, role, start, end, bullets
        - certifications: List[str] - keywords only
        """
        if not self.enabled:
            logger.info("LLM extraction disabled, returning empty result")
            return self._empty_result()

        if not raw_text or len(raw_text.strip()) < 50:
            logger.warning("CV text too short for LLM extraction")
            return self._empty_result()

        try:
            # Truncate very long CVs to stay within token limits
            text_for_extraction = raw_text[:15000]  # ~4k tokens

            extracted = self._call_openai_extraction(text_for_extraction)
            logger.info(f"LLM extraction successful: {extracted.get('name', 'Unknown')}")
            return extracted

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._empty_result()

    def _call_openai_extraction(self, text: str) -> Dict[str, Any]:
        """Call OpenAI API to extract CV data"""
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized")

        prompt = self._build_extraction_prompt(text)

        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume parser. Extract structured information from resumes with high accuracy.

IMPORTANT INSTRUCTIONS:
1. For Basic Information:
   - Extract the candidate's full name (usually at the top)
   - Extract email address (look for @ symbol)
   - Extract location (city, state/country)

2. For Summary:
   - Extract the professional summary or objective section
   - If no explicit summary, create a brief one from the first paragraph or key highlights
   - Keep it concise (2-3 sentences max)

3. For Skills:
   - Extract ONLY skill keywords (technologies, tools, methodologies)
   - Return as a list of individual skills
   - Include programming languages, frameworks, tools, certifications
   - Normalize case (lowercase)

4. For Experience:
   - Extract all work experience entries
   - For each entry include: organization, role, start date, end date, and bullet points
   - Preserve the original bullet points

5. For Certifications:
   - Extract ONLY certification keywords/names
   - Return as a list of certification names
   - Include acronyms (AWS, PMP, etc.)

Return ONLY a valid JSON object. Do not include any explanations or markdown formatting."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
            )

            # Parse response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            # Validate and normalize the response
            return self._normalize_extraction(result_json)

        except Exception as e:
            logger.error(f"OpenAI extraction call failed: {e}")
            raise

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for CV extraction"""
        prompt = f"""Extract structured information from this resume/CV:

{text}

Return a JSON object with this EXACT structure:
{{
  "name": "Full Name",
  "email": "email@example.com or null",
  "location": "City, State/Country or null",
  "summary": "Professional summary (2-3 sentences)",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "org": "Company Name",
      "role": "Job Title",
      "start": "Start Date (e.g., Jan 2020 or 2020)",
      "end": "End Date or 'present'",
      "bullets": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "certifications": ["Certification Name 1", "AWS Certified", "PMP"]
}}

IMPORTANT:
- For skills: return individual keywords only (e.g., ["python", "react", "aws"])
- For certifications: return certification names/acronyms only
- If a field is not found, use null for strings or [] for arrays
- Ensure all dates are extracted if available
- Extract ALL work experience entries, not just the most recent"""

        return prompt

    def _normalize_extraction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate extracted data"""
        normalized = {
            "name": str(data.get("name", "Unknown")).strip() or "Unknown",
            "email": data.get("email"),
            "location": data.get("location"),
            "summary": str(data.get("summary", "")).strip(),
            "skills": [],
            "experience": [],
            "certifications": [],
            "education": [],  # Keep for compatibility
        }

        # Normalize email
        if normalized["email"] and normalized["email"] != "null":
            normalized["email"] = str(normalized["email"]).strip().lower()
        else:
            normalized["email"] = None

        # Normalize location
        if normalized["location"] and normalized["location"] != "null":
            normalized["location"] = str(normalized["location"]).strip()
        else:
            normalized["location"] = None

        # Normalize skills - ensure they're lowercase keywords
        raw_skills = data.get("skills", [])
        if isinstance(raw_skills, list):
            for skill in raw_skills:
                if skill and isinstance(skill, str):
                    skill_clean = skill.strip().lower()
                    if skill_clean and len(skill_clean) > 1 and len(skill_clean) < 50:
                        normalized["skills"].append(skill_clean)

        # Deduplicate skills
        normalized["skills"] = list(set(normalized["skills"]))[:50]

        # Normalize experience
        raw_experience = data.get("experience", [])
        if isinstance(raw_experience, list):
            for exp in raw_experience[:15]:  # Limit to 15 entries
                if isinstance(exp, dict):
                    exp_item = {
                        "org": str(exp.get("org", "")).strip()[:100] or "",
                        "role": str(exp.get("role", "")).strip()[:100] or "",
                        "start": str(exp.get("start", "")).strip() if exp.get("start") else None,
                        "end": str(exp.get("end", "")).strip() if exp.get("end") else None,
                        "bullets": []
                    }

                    # Normalize bullets
                    bullets = exp.get("bullets", [])
                    if isinstance(bullets, list):
                        for bullet in bullets[:10]:  # Limit to 10 bullets per job
                            if bullet and isinstance(bullet, str):
                                bullet_clean = bullet.strip()
                                if bullet_clean:
                                    exp_item["bullets"].append(bullet_clean)

                    normalized["experience"].append(exp_item)

        # Normalize certifications - ensure they're keywords
        raw_certs = data.get("certifications", [])
        if isinstance(raw_certs, list):
            for cert in raw_certs:
                if cert and isinstance(cert, str):
                    cert_clean = cert.strip()
                    if cert_clean and len(cert_clean) > 1 and len(cert_clean) < 150:
                        normalized["certifications"].append(cert_clean)

        # Deduplicate certifications
        normalized["certifications"] = list(set(normalized["certifications"]))[:20]

        return normalized

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty extraction result"""
        return {
            "name": "Unknown",
            "email": None,
            "location": None,
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
        }


def get_llm_extraction_service() -> LLMExtractionService:
    """Get LLM extraction service singleton"""
    return LLMExtractionService()
