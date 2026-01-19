"""Resume parser implementation"""
import io
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

import docx
from pdfminer.high_level import extract_text as extract_pdf_text

from app.core.logging import get_logger
from app.services.ocr import ocr_service
from app.services.llm_extraction import get_llm_extraction_service

logger = get_logger(__name__)

T = TypeVar('T')


class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


def run_with_timeout(func: Callable[[], T], timeout_seconds: int) -> Optional[T]:
    """Run a function with a timeout, works on all platforms"""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds")
    except Exception as e:
        logger.error(f"Function execution failed: {e}")
        raise


class ResumeParser:
    """Parse resumes from PDF, DOCX, or text formats"""

    def parse(self, content: bytes, mime_type: str, use_ocr: bool = False) -> dict:
        """Parse resume and extract structured information"""
        # Extract raw text
        text = self._extract_text(content, mime_type, use_ocr)

        if not text or len(text.strip()) < 50:
            logger.warning("Extracted text too short or empty")
            return self._empty_result()

        # Try LLM extraction first for consistent data extraction
        llm_service = get_llm_extraction_service()
        if llm_service.enabled:
            try:
                logger.info("Attempting LLM-based CV extraction")
                llm_parsed = llm_service.extract_cv_data(text)

                # Validate LLM extraction - ensure we got meaningful data
                if (llm_parsed.get("name") and llm_parsed.get("name") != "Unknown" and
                    (llm_parsed.get("skills") or llm_parsed.get("experience"))):
                    # LLM extraction successful, use it
                    llm_parsed["raw_text"] = text
                    logger.info(f"LLM extraction successful for: {llm_parsed.get('name')}")
                    return llm_parsed
                else:
                    logger.warning("LLM extraction returned insufficient data, falling back to regex")
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to regex: {e}")
        else:
            logger.info("LLM extraction disabled, using regex-based extraction")

        # Fallback: Parse structured sections using regex
        parsed = {
            "summary": self._extract_summary(text),
            "skills": self._extract_skills(text),
            "experience": self._extract_experience(text),
            "education": self._extract_education(text),
            "certifications": self._extract_certifications(text),
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "location": self._extract_location(text),
            "raw_text": text,
        }

        return parsed

    def _extract_text(self, content: bytes, mime_type: str, use_ocr: bool) -> str:
        """Extract text from document based on mime type"""
        try:
            if "pdf" in mime_type.lower():
                text = ""

                # Try pdfplumber first for better multi-column layout handling (with timeout)
                try:
                    logger.info("Attempting pdfplumber extraction with 30s timeout")
                    text = run_with_timeout(
                        lambda: self._extract_pdf_with_pdfplumber(content),
                        timeout_seconds=30
                    )
                    if not text:
                        text = ""
                except TimeoutException:
                    logger.warning("pdfplumber extraction timed out after 30s, skipping to pdfminer")
                    text = ""
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
                    text = ""

                # Fallback to pdfminer if pdfplumber fails or returns too little text
                if not text or len(text.strip()) < 100:
                    logger.info("pdfplumber extraction insufficient, trying pdfminer with 30s timeout")
                    try:
                        text = run_with_timeout(
                            lambda: extract_pdf_text(io.BytesIO(content)),
                            timeout_seconds=30
                        )
                        if not text:
                            text = ""
                    except TimeoutException:
                        logger.warning("pdfminer extraction timed out after 30s")
                        text = ""
                    except Exception as e:
                        logger.warning(f"pdfminer extraction failed: {e}")
                        text = ""

                # If text is still too short and OCR is enabled, try OCR
                if use_ocr and len(text.strip()) < 100 and ocr_service.available:
                    logger.info("PDF text too short, attempting OCR with 60s timeout")
                    try:
                        ocr_text = run_with_timeout(
                            lambda: ocr_service.extract_text_from_pdf(content),
                            timeout_seconds=60
                        )
                        if ocr_text:
                            text = ocr_text
                    except TimeoutException:
                        logger.warning("OCR extraction timed out after 60s")
                    except Exception as e:
                        logger.warning(f"OCR extraction failed: {e}")

                return text
            elif "word" in mime_type.lower() or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(io.BytesIO(content))
                return "\n".join([para.text for para in doc.paragraphs])
            elif "text" in mime_type.lower():
                return content.decode("utf-8", errors="ignore")
            else:
                logger.warning(f"Unsupported mime type: {mime_type}")
                return content.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    def _extract_pdf_with_pdfplumber(self, content: bytes) -> str:
        """Extract text from PDF using pdfplumber for better layout handling"""
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                # Limit to first 20 pages to prevent extremely long processing times
                max_pages = min(len(pdf.pages), 20)
                logger.info(f"Processing {max_pages} pages with pdfplumber")

                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        # Extract text with layout preservation
                        page_text = page.extract_text(layout=True)
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {i+1}: {e}")
                        continue

            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("pdfplumber not installed, falling back to pdfminer")
            return ""
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""

    def _extract_summary(self, text: str) -> str:
        """Extract summary/objective section"""
        # Look for summary section
        patterns = [
            r"(?i)(?:summary|objective|profile)[\s:]*\n(.*?)(?=\n(?:experience|education|skills|employment)|\Z)",
            r"^(.*?)(?=\n(?:experience|education|skills|employment))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:
                    return summary[:500]
        # Fallback: first 3 lines
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return " ".join(lines[:3])[:500]

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        skills = []
        # Look for skills section
        match = re.search(
            r"(?i)(?:skills|technical skills|technologies)[\s:]*\n(.*?)(?=\n(?:experience|education|certifications)|\Z)",
            text,
            re.DOTALL,
        )
        if match:
            skills_text = match.group(1)
            # Split by common separators
            tokens = re.split(r"[,;•\|\n]", skills_text)
            for token in tokens:
                skill = token.strip()
                if skill and len(skill) > 1 and len(skill) < 50:
                    skills.append(skill.lower())

        # Also look for inline skills patterns
        tech_keywords = re.findall(
            r"\b(?:python|java|javascript|typescript|react|node|docker|kubernetes|aws|azure|gcp|sql|nosql|terraform|ansible|jenkins|git|ci/cd)\b",
            text,
            re.IGNORECASE,
        )
        skills.extend([k.lower() for k in tech_keywords])

        return list(set(skills))[:50]

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experience = []
        # Look for experience section
        match = re.search(
            r"(?i)(?:experience|employment|work history)[\s:]*\n(.*?)(?=\n(?:education|certifications|skills)|\Z)",
            text,
            re.DOTALL,
        )
        if not match:
            return []

        exp_text = match.group(1)
        # Split by date patterns or blank lines
        entries = re.split(r"\n\s*\n", exp_text)

        for entry in entries[:10]:
            if len(entry.strip()) < 20:
                continue

            exp_item = {
                "org": self._extract_org(entry),
                "role": self._extract_role(entry),
                "start": self._extract_start_date(entry),
                "end": self._extract_end_date(entry),
                "bullets": self._extract_bullets(entry),
            }
            experience.append(exp_item)

        return experience

    def _extract_org(self, entry: str) -> str:
        """Extract organization name from experience entry"""
        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        if lines:
            # Often the first line or after role
            return lines[0][:100]
        return ""

    def _extract_role(self, entry: str) -> str:
        """Extract role/title from experience entry"""
        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        for line in lines[:3]:
            if any(word in line.lower() for word in ["engineer", "developer", "manager", "lead", "architect", "analyst"]):
                return line[:100]
        return ""

    def _extract_start_date(self, entry: str) -> Optional[str]:
        """Extract start date from entry"""
        # Look for date patterns
        match = re.search(r"(\d{4}|\w+ \d{4})", entry)
        if match:
            return match.group(1)
        return None

    def _extract_end_date(self, entry: str) -> Optional[str]:
        """Extract end date from entry"""
        if re.search(r"(?i)\b(?:present|current|now)\b", entry):
            return "present"
        # Look for second date
        dates = re.findall(r"(\d{4}|\w+ \d{4})", entry)
        if len(dates) >= 2:
            return dates[1]
        return None

    def _extract_bullets(self, entry: str) -> List[str]:
        """Extract bullet points from entry"""
        bullets = []
        lines = entry.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("•", "-", "*")) or (len(stripped) > 30 and not self._is_header_line(stripped)):
                bullets.append(stripped.lstrip("•-* "))
        return bullets[:10]

    def _is_header_line(self, line: str) -> bool:
        """Check if line looks like a header"""
        return len(line) < 50 and not line.endswith((".", "!"))

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education"""
        education = []
        match = re.search(
            r"(?i)(?:education)[\s:]*\n(.*?)(?=\n(?:experience|certifications|skills)|\Z)",
            text,
            re.DOTALL,
        )
        if match:
            edu_text = match.group(1)
            entries = re.split(r"\n\s*\n", edu_text)
            for entry in entries[:5]:
                if len(entry.strip()) > 10:
                    education.append({
                        "degree": entry.strip()[:200],
                        "year": self._extract_year(entry),
                    })
        return education

    def _extract_year(self, text: str) -> Optional[str]:
        """Extract year from text"""
        match = re.search(r"\b(19|20)\d{2}\b", text)
        if match:
            return match.group(0)
        return None

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certs = []
        match = re.search(
            r"(?i)(?:certifications?|certificates?)[\s:]*\n(.*?)(?=\n(?:experience|education|skills)|\Z)",
            text,
            re.DOTALL,
        )
        if match:
            cert_text = match.group(1)
            lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
            for line in lines[:10]:
                if len(line) > 5:
                    certs.append(line[:150])
        return certs

    def _extract_name(self, text: str) -> str:
        """Extract candidate name (usually first line)"""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            first_line = lines[0]
            # Name is usually the first line, not too long
            if len(first_line) < 50 and not "@" in first_line:
                return first_line
        return "Unknown"

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if match:
            return match.group(0)
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        # Common phone number patterns
        patterns = [
            r"\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})",  # US format: (123) 456-7890, 123-456-7890, +1 123 456 7890
            r"\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}",  # International formats
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Return the full matched phone number
                return match.group(0).strip()
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location"""
        # Look for city, state patterns
        match = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\b", text)
        if match:
            return match.group(0)
        return None

    def _empty_result(self) -> dict:
        """Return empty parsed result"""
        return {
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "name": "Unknown",
            "email": None,
            "phone": None,
            "location": None,
            "raw_text": "",
        }
