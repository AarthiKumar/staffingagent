"""Ranking service with config-driven scoring"""
from datetime import datetime
from typing import Any, Dict, List

from app.core.config import AgentConfig
from app.core.logging import get_logger
from app.models import Section

logger = get_logger(__name__)


class RankingService:
    """Rank candidates using weighted scoring"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = AgentConfig(agent_id)
        self.weights = self.config.get("ranking.weights", {})

    def rank_results(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any],
        sections_map: Dict[str, List[Section]],
    ) -> List[Dict[str, Any]]:
        """Rank results using weighted scoring"""

        for result in results:
            candidate_id = result["candidate_id"]
            sections = sections_map.get(candidate_id, [])

            # Compute individual scores
            cosine_score = result.get("cosine_similarity", 0.0)
            skills_score = self._compute_skills_score(sections, filters.get("required_skills", []))
            cert_score = self._compute_cert_score(sections, filters.get("required_certs", []))
            recency_score = self._compute_recency_score(result["candidate"])

            # Weighted total
            total_score = (
                self.weights.get("cosine", 0.55) * cosine_score
                + self.weights.get("skills", 0.25) * skills_score
                + self.weights.get("cert", 0.10) * cert_score
                + self.weights.get("recency", 0.10) * recency_score
            )

            result["score"] = round(total_score, 4)
            result["score_breakdown"] = {
                "cosine": round(cosine_score, 4),
                "skills": round(skills_score, 4),
                "cert": round(cert_score, 4),
                "recency": round(recency_score, 4),
            }

        # Sort by total score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _compute_skills_score(self, sections: List[Section], required_skills: List[str]) -> float:
        """Compute skills match score"""
        if not required_skills:
            return 1.0

        # Check how many required skills are mentioned in sections
        skills_text = " ".join([s.text.lower() for s in sections if s.type == "skills"])
        matched = sum(1 for skill in required_skills if skill.lower() in skills_text)

        return matched / len(required_skills) if required_skills else 0.0

    def _compute_cert_score(self, sections: List[Section], required_certs: List[str]) -> float:
        """Compute certification match score"""
        if not required_certs:
            return 1.0

        certs_text = " ".join([s.text.lower() for s in sections if s.type == "certifications"])
        matched = sum(1 for cert in required_certs if cert.lower() in certs_text)

        return matched / len(required_certs) if required_certs else 0.0

    def _compute_recency_score(self, candidate) -> float:
        """Compute recency score based on last update"""
        # More recent updates get higher scores
        days_since_update = (datetime.utcnow() - candidate.updated_at).days
        # Decay over 365 days
        score = max(0.0, 1.0 - (days_since_update / 365.0))
        return score

    def build_explanation(
        self,
        result: Dict[str, Any],
        filters: Dict[str, Any],
        sections: List[Section],
    ) -> Dict[str, Any]:
        """Build 'why' explanation for a result"""
        required_skills = filters.get("required_skills", [])
        required_certs = filters.get("required_certs", [])

        # Find matched skills
        matched_skills = []
        skills_text = " ".join([s.text.lower() for s in sections if s.type == "skills"])
        for skill in required_skills:
            if skill.lower() in skills_text:
                matched_skills.append(skill)

        # Find matched certs
        matched_certs = []
        certs_text = " ".join([s.text.lower() for s in sections if s.type == "certifications"])
        for cert in required_certs:
            if cert.lower() in certs_text:
                matched_certs.append(cert)

        # Extract relevant snippets
        snippets = []
        for section in sections[:5]:
            if section.type in ("experience", "summary"):
                snippets.append({
                    "section": section.type,
                    "text": section.text[:200],
                    "start": section.start_idx or 0,
                    "end": section.end_idx or len(section.text),
                })

        return {
            "skills": matched_skills,
            "certs": matched_certs,
            "snippets": snippets,
        }
