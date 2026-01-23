"""Normalization service for skills and certifications"""
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class NormalizeService:
    """Normalize skills and certifications using ontology CSVs with enhanced matching"""

    def __init__(self, skills_csv: str, aliases_csv: str, certs_csv: str):
        self.skills: Set[str] = self._load_skills(skills_csv)
        self.aliases: Dict[str, str] = self._load_aliases(aliases_csv)
        self.certs: Set[str] = self._load_certs(certs_csv)

        # Build reverse lookup: canonical -> all variants (for text scanning)
        self.skill_variants: Dict[str, List[str]] = self._build_skill_variants()
        self.cert_variants: Dict[str, List[str]] = self._build_cert_variants()

    def _norm(self, s: str) -> str:
        """Normalize string: lowercase, strip, collapse whitespace"""
        s = (s or "").strip().lower()
        s = re.sub(r"\s+", " ", s)
        return s

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
                    if "name" in row and row["name"].strip():
                        skills.add(self._norm(row["name"]))
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
                        alias = self._norm(row["alias"])
                        canonical = self._norm(row["canonical"])
                        if alias and canonical:
                            aliases[alias] = canonical
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
                    if "name" in row and row["name"].strip():
                        certs.add(self._norm(row["name"]))
        except Exception as e:
            logger.error(f"Error loading certs CSV: {e}")

        return certs

    def _build_skill_variants(self) -> Dict[str, List[str]]:
        """Build map of canonical skill -> all its variants (aliases + canonical)"""
        variants = {}

        # Add canonical skills
        for skill in self.skills:
            variants[skill] = [skill]

        # Add aliases
        for alias, canonical in self.aliases.items():
            if canonical in variants:
                variants[canonical].append(alias)
            else:
                # Canonical not in skills.csv, but referenced in aliases
                variants[canonical] = [canonical, alias]

        return variants

    def _build_cert_variants(self) -> Dict[str, List[str]]:
        """Build map of canonical cert -> all its variants"""
        variants = {}
        for cert in self.certs:
            variants[cert] = [cert]
        return variants

    def normalize_skill(self, skill: str) -> str:
        """Normalize a skill to canonical form"""
        skill_lower = self._norm(skill)

        # Check if it's an alias
        if skill_lower in self.aliases:
            return self.aliases[skill_lower]

        # Check if it's already canonical
        if skill_lower in self.skills:
            return skill_lower

        # Conservative substring match (require length >= 4 to avoid false positives)
        if len(skill_lower) >= 4:
            for canonical in self.skills:
                if len(canonical) >= 4 and canonical in skill_lower:
                    return canonical

        # Return as-is if not found
        return skill_lower

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize a list of skills"""
        normalized = [self.normalize_skill(s) for s in skills if s and s.strip()]
        # Deduplicate while preserving canonical order
        seen = set()
        result = []
        for s in normalized:
            if s not in seen:
                seen.add(s)
                result.append(s)
        return result

    def match_skill_with_evidence(self, term: str) -> Optional[Dict]:
        """
        Match a term to ontology and return match details with evidence.
        Returns: {"canonical": str, "confidence": float, "evidence": str} or None
        """
        term_norm = self._norm(term)
        if not term_norm:
            return None

        # Exact alias match
        if term_norm in self.aliases:
            canonical = self.aliases[term_norm]
            return {
                "canonical": canonical,
                "confidence": 0.95,
                "evidence": f"alias match: '{term}' -> '{canonical}'"
            }

        # Exact canonical match
        if term_norm in self.skills:
            return {
                "canonical": term_norm,
                "confidence": 1.0,
                "evidence": f"exact canonical match: '{term}'"
            }

        # Conservative substring match
        if len(term_norm) >= 4:
            for canonical in self.skills:
                if len(canonical) >= 4 and canonical in term_norm:
                    return {
                        "canonical": canonical,
                        "confidence": 0.85,
                        "evidence": f"substring match: '{canonical}' found in '{term}'"
                    }

        return None

    def find_skills_in_text(self, text: str) -> List[Dict]:
        """
        Scan text for skill mentions using word-boundary pattern matching.
        Returns list of: {"canonical": str, "confidence": float, "evidence": str}
        """
        if not text:
            return []

        text_norm = " " + self._norm(text) + " "
        matches = {}

        for canonical, variants in self.skill_variants.items():
            for variant in variants:
                if not variant or len(variant) < 2:
                    continue

                # Word boundary-ish pattern (avoid embedded matches)
                pattern = r"(?<!\w)" + re.escape(variant) + r"(?!\w)"
                if re.search(pattern, text_norm):
                    matches[canonical] = {
                        "canonical": canonical,
                        "confidence": 0.90,
                        "evidence": f"found phrase: '{variant}' in text"
                    }
                    break  # Stop after first variant match for this skill

        return list(matches.values())

    def normalize_experience_skills(self, experience: Dict) -> Dict:
        """
        Enhance experience dict with detected skills.
        Adds: skills_normalized, skills_map
        Scans: org, role, bullets
        """
        org = experience.get("org", "")
        role = experience.get("role", "")
        bullets = experience.get("bullets", [])

        text_blob = "\n".join([org, role, *bullets])

        skill_matches = self.find_skills_in_text(text_blob)

        # Deduplicate by canonical
        canonical_set = {m["canonical"] for m in skill_matches}
        skills_normalized = sorted(canonical_set)

        exp_enhanced = dict(experience)
        exp_enhanced["skills_normalized"] = skills_normalized
        exp_enhanced["skills_map"] = skill_matches

        return exp_enhanced

    def is_valid_cert(self, cert: str) -> bool:
        """Check if certification is in ontology"""
        return self._norm(cert) in self.certs

    def normalize_cert(self, cert: str) -> str:
        """Normalize certification name"""
        cert_lower = self._norm(cert)

        # Exact match first
        if cert_lower in self.certs:
            return cert_lower

        # Fuzzy match against known certs
        for known_cert in self.certs:
            if len(known_cert) >= 4 and (known_cert in cert_lower or cert_lower in known_cert):
                return known_cert

        return cert_lower

    def normalize_certs(self, certs: List[str]) -> List[str]:
        """Normalize a list of certifications"""
        normalized = [self.normalize_cert(c) for c in certs if c and c.strip()]
        # Deduplicate
        seen = set()
        result = []
        for c in normalized:
            if c not in seen:
                seen.add(c)
                result.append(c)
        return result

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
            detected_skills = self.find_skills_in_text(all_text)

            for skill_match in detected_skills:
                skill = skill_match["canonical"]
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
