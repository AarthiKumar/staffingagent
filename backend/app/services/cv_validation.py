"""
Validation utilities for CV data extraction.
Filters out irrelevant data like passport numbers, IDs, personal info from skills/certifications.
"""
import re
from typing import List


class CVDataValidator:
    """Validates and filters extracted CV data"""

    # Patterns for data that should NOT be in skills or certifications
    INVALID_PATTERNS = [
        # Passport numbers (various formats)
        r"\b[A-Z]{1,2}[0-9]{6,9}\b",  # UK: A1234567, India: A1234567, etc.
        r"\b[0-9]{9}\b",  # US: 123456789
        r"\b[A-Z][0-9]{8}\b",  # Many countries: A12345678
        r"passport\s*(?:no|number|#)?\s*:?\s*[A-Z0-9]+",  # "Passport: X1234567"
        r"passport\s+[A-Z][0-9]{7,9}",  # "Passport A1234567"

        # National IDs, SSN, other government IDs
        r"\b\d{3}-\d{2}-\d{4}\b",  # US SSN: 123-45-6789
        r"\b\d{9,12}\b",  # Generic long numbers (Aadhaar, etc.)
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",  # PAN: ABCDE1234F
        r"(?:aadhar|aadhaar|pan|ssn|national\s+id)\s*(?:no|number|#)?\s*:?\s*[A-Z0-9\-]+",  # ID keywords
        r"\bpan\s*:?\s*[A-Z]{5}[0-9]{4}[A-Z]\b",  # PAN with label

        # Phone numbers
        r"\+?\d{1,4}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{3,4}[\s\-\.]?\d{3,4}",  # International/local
        r"\b\d{10}\b",  # 10-digit phone
        r"(?:phone|mobile|cell|tel)\s*:?\s*\+?[\d\s\-\(\)\.]+",  # Phone with label

        # Email addresses
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",

        # Dates (various formats) - enhanced to catch more variations
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # DD/MM/YYYY, MM-DD-YYYY
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",  # Jan 1, 2020
        r"\b\d{4}-\d{2}-\d{2}\b",  # ISO: 2020-01-01
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",  # Full month
        r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b",  # 1 Jan 2020
        r"(?:dob|date\s+of\s+birth|born)\s*:?\s*\d",  # Date of birth

        # URLs
        r"https?://[^\s]+",
        r"www\.[^\s]+",
        r"\b[a-z]+\.(?:com|org|net|edu|gov|io|co)\b",  # Domain names

        # Address-like patterns
        r"\b\d+\s+[A-Z][a-z]+\s+(street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|boulevard|blvd)\b",
        r"(?:address|location)\s*:?\s*\d+",  # Address with label

        # ZIP/Postal codes
        r"\b\d{5}(?:-\d{4})?\b",  # US ZIP
        r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b",  # Canadian postal
        r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b",  # UK postcode
        r"\b\d{6}\b",  # Indian PIN code (6 digits)

        # License plates and driver's license
        r"\b[A-Z]{2,3}[\s-]?\d{1,4}[\s-]?[A-Z]{0,3}\b",
        r"(?:license|licence|dl)\s*(?:no|number|#)?\s*:?\s*[A-Z0-9\-]+",  # License with label

        # Credit card-like long numbers
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",

        # Personal info keywords that sometimes leak into skills
        r"\b(?:father|mother|spouse|husband|wife)(?:'s)?\s+name\b",
        r"\b(?:male|female|married|single|divorced)\b",
        r"\bage\s*:?\s*\d+",
        r"\b\d+\s*(?:years|yrs)\s+old\b",
        r"\bnationality\s*:?\s*[a-z]+",
        r"\bvisa\s+(?:status|type)\b",

        # Page numbers and CV metadata
        r"\bpage\s+\d+(?:\s+of\s+\d+)?\b",
        r"\b\d+\s+of\s+\d+\b",  # "1 of 2"
        r"\bcv\s+updated\b",
        r"\bversion\s+\d+\b",

        # Reference-related text
        r"\bavailable\s+(?:upon|on)\s+request\b",
        r"\breferences\s+available\b",
        r"\bconfidential\b",

        # Salary and compensation
        r"\b\d+(?:,\d{3})*(?:\s+(?:usd|inr|eur|gbp|dollars?|rupees?))?\b",  # Amounts
        r"\b(?:salary|compensation|ctc|package)\s*:?\s*\d",  # Salary with label
        r"\blpa\b",  # Lakhs per annum
        r"\b\d+\s*(?:lpa|lacs?|lakhs?)\b",  # Indian salary format
    ]

    # Common non-skill words that appear in skills sections
    NOISE_WORDS = {
        "proficient", "experience", "knowledge", "familiar", "expert", "advanced",
        "intermediate", "beginner", "years", "including", "such as", "etc",
        "and", "or", "with", "using", "used", "the", "a", "an", "of", "in",
        "for", "to", "on", "at", "from", "by", "as", "is", "was", "are",
        "have", "has", "had", "can", "will", "would", "should", "could",
        "page", "cv", "resume", "curriculum vitae", "confidential",
        "personal information", "contact", "references", "available upon request",
        "skills", "technical skills", "core competencies", "technologies",
        "tools", "platforms", "software", "applications", "systems",
        "good", "excellent", "strong", "working", "hands-on", "practical",
        "theoretical", "basic", "sound", "extensive", "limited", "exposure",
        "description", "summary", "overview", "details", "information",
        "section", "list", "items", "points", "bullet", "bullets",
        "professional", "technical", "business", "functional", "soft",
        "personal", "interpersonal", "communication", "teamwork", "leadership",
        "proficiency", "competency", "ability", "capability", "capacity",
        "duration", "period", "span", "length", "time", "currently", "present"
    }

    # Generic phrases that indicate personal data section
    PERSONAL_INFO_INDICATORS = [
        "passport", "date of birth", "dob", "nationality", "marital status",
        "gender", "visa", "driving license", "licence", "social security",
        "national id", "pan card", "aadhaar", "aadhar"
    ]

    # Known valid 2-character technical terms
    VALID_SHORT_SKILLS = {
        "c#", "c++", "go", "r", "js", "ts", "ai", "ml", "ci", "cd",
        "qa", "ui", "ux", "vr", "ar", "3d", "api", "sql", "css", "ios"
    }

    @staticmethod
    def is_valid_skill(skill: str) -> bool:
        """
        Check if a skill string is valid (not personal data, ID, etc.)

        Args:
            skill: The skill string to validate

        Returns:
            True if valid skill, False if invalid/personal data
        """
        if not skill or not isinstance(skill, str):
            return False

        skill_lower = skill.lower().strip()
        skill_clean = skill.strip()

        # Check if it's a known valid short skill (e.g., c#, go, r)
        if skill_lower in CVDataValidator.VALID_SHORT_SKILLS:
            return True

        # Basic length checks - minimum 3 characters for generic skills
        # (Known 2-char skills are whitelisted above)
        if len(skill_clean) < 3 or len(skill_clean) > 100:
            return False

        # Check if it's pure numbers (likely ID/passport)
        if skill_clean.replace(" ", "").replace("-", "").isdigit():
            return False

        # Check for personal info indicators
        for indicator in CVDataValidator.PERSONAL_INFO_INDICATORS:
            if indicator in skill_lower:
                return False

        # Check against invalid patterns
        for pattern in CVDataValidator.INVALID_PATTERNS:
            if re.search(pattern, skill_clean, re.IGNORECASE):
                return False

        # Check if it's just noise words
        if skill_lower in CVDataValidator.NOISE_WORDS:
            return False

        # Check if it starts with noise words
        for noise in CVDataValidator.NOISE_WORDS:
            if skill_lower.startswith(noise + " "):
                return False

        # Reject if it has too many numbers relative to letters
        num_count = sum(c.isdigit() for c in skill_clean)
        letter_count = sum(c.isalpha() for c in skill_clean)

        if letter_count > 0:
            number_ratio = num_count / (num_count + letter_count)
            if number_ratio > 0.5:  # More than 50% numbers is suspicious
                return False

        # Reject pure special characters or very short alphanumeric strings
        if not any(c.isalpha() for c in skill_clean):
            return False

        return True

    @staticmethod
    def is_valid_certification(cert: str) -> bool:
        """
        Check if a certification string is valid (not personal data, ID, etc.)

        Args:
            cert: The certification string to validate

        Returns:
            True if valid certification, False if invalid/personal data
        """
        if not cert or not isinstance(cert, str):
            return False

        cert_lower = cert.lower().strip()
        cert_clean = cert.strip()

        # Basic length checks - certifications can be longer than skills
        if len(cert_clean) < 3 or len(cert_clean) > 200:
            return False

        # Check if it's pure numbers (likely ID)
        if cert_clean.replace(" ", "").replace("-", "").isdigit():
            return False

        # Check for personal info indicators
        for indicator in CVDataValidator.PERSONAL_INFO_INDICATORS:
            if indicator in cert_lower:
                return False

        # Check against invalid patterns
        for pattern in CVDataValidator.INVALID_PATTERNS:
            if re.search(pattern, cert_clean, re.IGNORECASE):
                return False

        # Reject if it's just noise words
        if cert_lower in CVDataValidator.NOISE_WORDS:
            return False

        # Must have some alphabetic characters
        if not any(c.isalpha() for c in cert_clean):
            return False

        # Check for common certification indicators (positive signals)
        cert_indicators = [
            "certified", "certification", "certificate", "professional",
            "associate", "expert", "specialist", "accredited", "licensed",
            "diploma", "degree", "training", "course", "program"
        ]

        has_cert_indicator = any(indicator in cert_lower for indicator in cert_indicators)

        # If it has cert indicators, be more lenient
        if has_cert_indicator:
            return True

        # Otherwise apply stricter validation
        # Reject if too many numbers relative to letters
        num_count = sum(c.isdigit() for c in cert_clean)
        letter_count = sum(c.isalpha() for c in cert_clean)

        if letter_count > 0:
            number_ratio = num_count / (num_count + letter_count)
            if number_ratio > 0.6:  # More than 60% numbers is suspicious
                return False

        return True

    @staticmethod
    def filter_skills(skills: List[str]) -> List[str]:
        """
        Filter a list of skills to remove invalid entries

        Args:
            skills: List of skill strings

        Returns:
            Filtered list of valid skills
        """
        return [
            skill.strip()
            for skill in skills
            if CVDataValidator.is_valid_skill(skill)
        ]

    @staticmethod
    def filter_certifications(certs: List[str]) -> List[str]:
        """
        Filter a list of certifications to remove invalid entries

        Args:
            certs: List of certification strings

        Returns:
            Filtered list of valid certifications
        """
        return [
            cert.strip()
            for cert in certs
            if CVDataValidator.is_valid_certification(cert)
        ]
