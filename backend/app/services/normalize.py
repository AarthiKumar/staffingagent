"""Normalization service for skills and certifications"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from app.core.logging import get_logger

logger = get_logger(__name__)


class NormalizeService:
    """Normalize skills and certifications using ontology CSVs"""

    def __init__(self, skills_csv: str, aliases_csv: str, certs_csv: str):
        self.skills: Set[str] = self._load_skills(skills_csv)
        self.aliases: Dict[str, str] = self._load_aliases(aliases_csv)
        self.certs: Set[str] = self._load_certs(certs_csv)

    def _load_skills(self, csv_path: str) -> Set[str]:
        """Load canonical skills from CSV"""
        skills = set()
        path = Path(csv_path)
        if not path.exists():
            logger.warning(f"Skills CSV not found: {csv_path}")
            return skills

        try:
            with open(path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "name" in row:
                        skills.add(row["name"].lower().strip())
        except Exception as e:
            logger.error(f"Error loading skills CSV: {e}")

        return skills

    def _load_aliases(self, csv_path: str) -> Dict[str, str]:
        """Load skill aliases from CSV"""
        aliases = {}
        path = Path(csv_path)
        if not path.exists():
            logger.warning(f"Aliases CSV not found: {csv_path}")
            return aliases

        try:
            with open(path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "alias" in row and "canonical" in row:
                        aliases[row["alias"].lower().strip()] = row["canonical"].lower().strip()
        except Exception as e:
            logger.error(f"Error loading aliases CSV: {e}")

        return aliases

    def _load_certs(self, csv_path: str) -> Set[str]:
        """Load canonical certifications from CSV"""
        certs = set()
        path = Path(csv_path)
        if not path.exists():
            logger.warning(f"Certs CSV not found: {csv_path}")
            return certs

        try:
            with open(path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "name" in row:
                        certs.add(row["name"].lower().strip())
        except Exception as e:
            logger.error(f"Error loading certs CSV: {e}")

        return certs

    def normalize_skill(self, skill: str) -> str:
        """Normalize a skill to canonical form"""
        skill_lower = skill.lower().strip()

        # Check if it's an alias
        if skill_lower in self.aliases:
            return self.aliases[skill_lower]

        # Check if it's already canonical
        if skill_lower in self.skills:
            return skill_lower

        # Return as-is if not found
        return skill_lower

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize a list of skills"""
        normalized = [self.normalize_skill(s) for s in skills]
        return list(set(normalized))

    def is_valid_cert(self, cert: str) -> bool:
        """Check if certification is in ontology"""
        return cert.lower().strip() in self.certs

    def normalize_cert(self, cert: str) -> str:
        """Normalize certification name"""
        cert_lower = cert.lower().strip()
        # Fuzzy match against known certs
        for known_cert in self.certs:
            if known_cert in cert_lower or cert_lower in known_cert:
                return known_cert
        return cert_lower

    def compute_years_per_skill(self, experience: List[dict]) -> Dict[str, float]:
        """Compute years of experience per skill from experience list"""
        skill_years = {}

        for exp in experience:
            start = exp.get("start")
            end = exp.get("end", "present")
            bullets = exp.get("bullets", [])

            # Parse dates
            years = self._compute_duration_years(start, end)
            if years == 0:
                continue

            # Extract skills from bullets
            all_text = " ".join(bullets)
            for skill in self.skills:
                if skill in all_text.lower():
                    skill_years[skill] = skill_years.get(skill, 0.0) + years

        return skill_years

    def _compute_duration_years(self, start: str, end: str) -> float:
        """Compute duration in years between start and end dates"""
        if not start:
            return 0.0

        try:
            # Parse start date
            start_year = self._extract_year(start)
            if not start_year:
                return 0.0

            # Parse end date
            if end and end.lower() in ("present", "current", "now"):
                end_year = datetime.now().year
            else:
                end_year = self._extract_year(end) if end else datetime.now().year

            if not end_year:
                end_year = datetime.now().year

            return max(0.0, end_year - start_year)
        except Exception as e:
            logger.error(f"Error computing duration: {e}")
            return 0.0

    def _extract_year(self, date_str: str) -> int:
        """Extract year from date string"""
        import re

        match = re.search(r"\b(19|20)(\d{2})\b", date_str)
        if match:
            return int(match.group(0))
        return 0


def get_normalize_service(agent_id: str) -> NormalizeService:
    """Get normalize service for agent"""
    from app.core.config import AgentConfig

    config = AgentConfig(agent_id)
    skills_csv = config.get("ontology.skills_csv", "./config/skills.csv")
    aliases_csv = config.get("ontology.aliases_csv", "./config/aliases.csv")
    certs_csv = config.get("ontology.certs_csv", "./config/certs.csv")

    return NormalizeService(skills_csv, aliases_csv, certs_csv)
