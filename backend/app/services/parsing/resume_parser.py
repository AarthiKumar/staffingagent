"""Resume parser implementation"""
import io
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

import docx
from pdfminer.high_level import extract_text as extract_pdf_text

from app.core.logging import get_logger
from app.services.ocr import ocr_service
from app.services.llm_extraction import get_llm_extraction_service
from app.services.cv_validation import CVDataValidator

logger = get_logger(__name__)

# Suppress verbose pdfminer debug logs (token-level output)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.WARNING)
logging.getLogger("pdfminer.converter").setLevel(logging.WARNING)
logging.getLogger("pdfminer.psparser").setLevel(logging.WARNING)

T = TypeVar('T')


class TimeoutException(Exception):
    """Exception raised when operation times out"""
    pass


def run_with_timeout(func: Callable[[], T], timeout_seconds: int) -> Optional[T]:
    """Run a function with a timeout, works on all platforms"""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise TimeoutException(f"Operation timed out after {timeout_seconds} seconds") from exc
    except Exception as e:
        logger.error(f"Function execution failed: {e}")
        raise
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


class ResumeParser:
    """Parse resumes from PDF, DOCX, or text formats"""

    def parse(self, content: bytes, mime_type: str, use_ocr: bool = False) -> dict:
        """Parse resume and extract structured information"""
        logger.info(f"Starting CV parsing - mime_type: {mime_type}, use_ocr: {use_ocr}")

        # Extract raw text
        text = self._extract_text(content, mime_type, use_ocr)
        logger.info(f"Primary text extraction: {len(text) if text else 0} characters")

        llm_text = self._extract_text_for_llm(content, mime_type, text)
        logger.info(f"Layout-aware text extraction: {len(llm_text) if llm_text else 0} characters")

        if (not text or len(text.strip()) < 50) and llm_text and len(llm_text.strip()) >= 50:
            logger.info("Primary extraction was short; using layout-aware text instead")
            text = llm_text

        if not text or len(text.strip()) < 50:
            logger.warning(f"Extracted text too short or empty: {len(text) if text else 0} chars")
            return self._empty_result()

        # Log text preview for debugging
        preview = text[:200].replace('\n', ' ')
        logger.info(f"Text preview: {preview}...")

        # Regex parsing
        logger.info("Performing regex-based extraction")
        regex_parsed = self._parse_with_regex(text)
        logger.info(f"Regex extracted - Name: {regex_parsed.get('name')}, Email: {regex_parsed.get('email')}, "
                   f"Skills: {len(regex_parsed.get('skills', []))}, Experience: {len(regex_parsed.get('experience', []))}")

        # Try LLM extraction first for consistent data extraction
        llm_service = get_llm_extraction_service()
        llm_parsed = None
        if llm_service.enabled:
            try:
                logger.info("Attempting LLM-based CV extraction")
                llm_parsed = self._extract_llm_with_chunking(llm_service, llm_text or text)
                logger.info(f"LLM extraction completed - Name: {llm_parsed.get('name', 'Unknown')}, "
                           f"Email: {llm_parsed.get('email')}, Skills: {len(llm_parsed.get('skills', []))}, "
                           f"Experience: {len(llm_parsed.get('experience', []))}")
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to regex only: {e}")
                import traceback
                logger.debug(f"LLM extraction traceback: {traceback.format_exc()}")
        else:
            logger.info("LLM extraction disabled, using regex-based extraction only")

        # Merge results
        merged = self._merge_llm_and_regex(llm_parsed, regex_parsed)
        merged["raw_text"] = text

        # Apply ontology-based normalization with skill detection in experience
        merged = self._apply_normalization(merged)

        # Validate results
        is_valid, issues = self._validate_parsed_data(merged)
        if not is_valid:
            logger.warning(f"Parsing validation failed: {', '.join(issues)}")
            logger.warning(f"Parsed data: Name={merged.get('name')}, Email={merged.get('email')}, "
                          f"Phone={merged.get('phone')}, Skills: {len(merged.get('skills', []))} raw / "
                          f"{len(merged.get('skills_normalized', []))} normalized, "
                          f"Experience: {len(merged.get('experience', []))}")
        else:
            logger.info(f"Parsing successful: Name={merged.get('name')}, Email={merged.get('email')}, "
                       f"Phone={merged.get('phone')}, Skills: {len(merged.get('skills_normalized', []))} normalized")

        return merged

    def _extract_text(self, content: bytes, mime_type: str, use_ocr: bool) -> str:
        """Extract text from document based on mime type"""
        try:
            # Handle Word documents (.doc and .docx) - convert to PDF for better extraction
            if "word" in mime_type.lower() or mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                logger.info(f"Word document detected ({mime_type}), attempting PDF conversion for better extraction")
                try:
                    from app.services.document_conversion import conversion_service
                    pdf_bytes = conversion_service.word_to_pdf(content, mime_type)

                    if pdf_bytes:
                        logger.info(f"Successfully converted Word to PDF ({len(pdf_bytes)} bytes), using PDF extraction")
                        # Recursively call with PDF content
                        return self._extract_text(pdf_bytes, "application/pdf", use_ocr)
                    else:
                        logger.warning("Word to PDF conversion failed, falling back to direct Word extraction")
                except Exception as e:
                    logger.warning(f"Word to PDF conversion error: {e}, falling back to direct extraction")

                # Fallback: try direct DOCX extraction (only works for .docx, not .doc)
                try:
                    return self._extract_docx_text(content)
                except Exception as e:
                    logger.error(f"Direct Word extraction also failed: {e}")
                    return ""

            if "pdf" in mime_type.lower():
                text = ""

                # Try pdfplumber first for better multi-column layout handling (with timeout)
                try:
                    logger.info("Attempting pdfplumber extraction with 10s timeout")
                    text = run_with_timeout(
                        lambda: self._extract_pdf_with_pdfplumber(content),
                        timeout_seconds=10
                    )
                    if not text:
                        text = ""
                except TimeoutException:
                    logger.warning("pdfplumber extraction timed out after 10s, skipping to pdfminer")
                    text = ""
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
                    text = ""

                # Fallback to pdfminer if pdfplumber fails or returns too little text
                if not text or len(text.strip()) < 100:
                    logger.info("pdfplumber extraction insufficient, trying pdfminer with 10s timeout")
                    try:
                        text = run_with_timeout(
                            lambda: extract_pdf_text(io.BytesIO(content)),
                            timeout_seconds=10
                        )
                        if not text:
                            text = ""
                    except TimeoutException:
                        logger.warning("pdfminer extraction timed out after 10s")
                        text = ""
                    except Exception as e:
                        logger.warning(f"pdfminer extraction failed: {e}")
                        text = ""

                # If text is still too short and OCR is enabled, try OCR
                if use_ocr and len(text.strip()) < 100 and ocr_service.available:
                    logger.info("PDF text too short, attempting OCR with 20s timeout")
                    try:
                        ocr_text = run_with_timeout(
                            lambda: ocr_service.extract_text_from_pdf(content),
                            timeout_seconds=20
                        )
                        if ocr_text:
                            text = ocr_text
                    except TimeoutException:
                        logger.warning("OCR extraction timed out after 20s")
                    except Exception as e:
                        logger.warning(f"OCR extraction failed: {e}")

                return text

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

    def _extract_pdf_layout_text(self, content: bytes) -> str:
        """Extract layout-aware text from PDF for LLM input."""
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                max_pages = min(len(pdf.pages), 15)
                logger.info(f"Processing {max_pages} pages with pdfplumber layout extraction")

                for page in pdf.pages[:max_pages]:
                    words = page.extract_words(
                        x_tolerance=2,
                        y_tolerance=3,
                        use_text_flow=True,
                    )
                    if not words:
                        continue

                    page_width = page.width or 0
                    mid_x = page_width / 2 if page_width else None

                    if mid_x:
                        left_words = [w for w in words if w["x0"] < mid_x * 0.95]
                        right_words = [w for w in words if w["x0"] >= mid_x * 0.95]
                        columns = [left_words, right_words]
                    else:
                        columns = [words]

                    column_texts = []
                    for column in columns:
                        if not column:
                            continue
                        column_sorted = sorted(column, key=lambda w: (w["top"], w["x0"]))
                        lines = self._group_words_into_lines(column_sorted)
                        column_texts.append("\n".join(lines))

                    if column_texts:
                        text_parts.append("\n\n".join(column_texts))

            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("pdfplumber not installed for layout extraction")
            return ""
        except Exception as e:
            logger.warning(f"pdfplumber layout extraction failed: {e}")
            return ""

    def _group_words_into_lines(self, words: List[Dict[str, Any]]) -> List[str]:
        """Group extracted words into lines based on y-position."""
        lines: List[List[str]] = []
        current_line: List[str] = []
        current_top: Optional[float] = None
        line_threshold = 4

        for word in words:
            word_top = word.get("top")
            if current_top is None or abs(word_top - current_top) <= line_threshold:
                current_line.append(word["text"])
                current_top = word_top if current_top is None else current_top
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [word["text"]]
                current_top = word_top

        if current_line:
            lines.append(current_line)

        return [" ".join(line).strip() for line in lines if line]

    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX with section-aware formatting."""
        doc = docx.Document(io.BytesIO(content))
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = (para.style.name or "").lower() if para.style else ""
            if "heading" in style_name:
                lines.append(f"\n{text.upper()}\n")
            else:
                lines.append(text)
        return "\n".join(lines)

    def _extract_text_for_llm(self, content: bytes, mime_type: str, fallback_text: str) -> str:
        """Extract layout-aware text for LLM input based on document type."""
        # For Word documents, we'll already have converted them to PDF in _extract_text
        # So fallback_text will be the PDF-extracted text, which is good for LLM
        if "word" in mime_type.lower() or mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # Word documents are already converted to PDF in _extract_text, use fallback
            return fallback_text

        if "pdf" in mime_type.lower():
            # Skip duplicate layout extraction if primary extraction already has sufficient text
            # This saves 10+ seconds per CV
            if fallback_text and len(fallback_text.strip()) >= 500:
                logger.info("Primary extraction has sufficient text, skipping duplicate layout-aware extraction")
                return fallback_text

            try:
                logger.info("Primary text was short, attempting layout-aware extraction with 10s timeout")
                return run_with_timeout(
                    lambda: self._extract_pdf_layout_text(content),
                    timeout_seconds=10
                ) or fallback_text
            except TimeoutException:
                logger.warning("Layout-aware PDF extraction timed out after 10s, using fallback text")
            except Exception as e:
                logger.warning(f"Layout-aware PDF extraction failed, using fallback text: {e}")
            return fallback_text

        return fallback_text

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better parsing"""
        if not text:
            return ""

        # Remove excessive whitespace (but preserve paragraph structure)
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline

        # Normalize section headers - ensure blank lines before major sections
        section_keywords = [
            'SUMMARY', 'OBJECTIVE', 'PROFILE',
            'EXPERIENCE', 'EMPLOYMENT', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE',
            'EDUCATION', 'ACADEMIC BACKGROUND',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES',
            'CERTIFICATIONS', 'CERTIFICATES',
            'PROJECTS'
        ]

        for keyword in section_keywords:
            # Case-insensitive replacement with proper spacing
            pattern = r'(\n|^)(' + keyword + r')(\s*:?\s*\n)'
            text = re.sub(pattern, r'\n\n\2\3', text, flags=re.IGNORECASE)

        # Clean up extra spaces around punctuation
        text = re.sub(r'\s+([,;.])', r'\1', text)

        return text.strip()

    def _validate_parsed_data(self, parsed: dict) -> tuple[bool, list[str]]:
        """
        Validate if parsing produced meaningful results.
        Returns (is_valid, list_of_issues)
        """
        issues = []

        # Check name
        if not parsed.get("name") or parsed["name"] == "Unknown":
            issues.append("No name extracted")

        # Check contact info
        if not parsed.get("email") and not parsed.get("phone"):
            issues.append("No contact information (email/phone) extracted")

        # Check content
        has_skills = parsed.get("skills") and len(parsed["skills"]) > 0
        has_experience = parsed.get("experience") and len(parsed["experience"]) > 0
        has_text = len(parsed.get("raw_text", "")) > 200

        if not has_skills and not has_experience and not has_text:
            issues.append("No meaningful content extracted (no skills, experience, or text)")

        is_valid = len(issues) == 0
        return is_valid, issues

    def _parse_with_regex(self, text: str) -> Dict[str, Any]:
        """Parse structured sections using regex."""
        # Normalize text before parsing
        normalized_text = self._normalize_text(text)

        return {
            "summary": self._extract_summary(normalized_text),
            "skills": self._extract_skills(normalized_text),
            "experience": self._extract_experience(normalized_text),
            "education": self._extract_education(normalized_text),
            "certifications": self._extract_certifications(normalized_text),
            "name": self._extract_name(normalized_text),
            "email": self._extract_email(normalized_text),
            "phone": self._extract_phone(normalized_text),
            "location": self._extract_location(normalized_text),
            "raw_text": text,
        }

    def _extract_llm_with_chunking(self, llm_service: Any, text: str) -> Dict[str, Any]:
        """Extract CV data from LLM using chunked input for long documents."""
        if not text:
            return self._empty_result()

        max_length = 12000
        if len(text) <= max_length:
            return llm_service.extract_cv_data(text)

        chunks = self._chunk_text(text, max_length=5000, overlap=200)
        max_chunks = 4
        results = []
        for chunk in chunks[:max_chunks]:
            results.append(llm_service.extract_cv_data(chunk))

        return self._merge_llm_results(results)

    def _chunk_text(self, text: str, max_length: int, overlap: int) -> List[str]:
        """Split text into chunks with overlap to preserve context."""
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        chunks = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= max_length:
                current = candidate
                continue

            if current:
                chunks.append(current)
            if len(paragraph) > max_length:
                for i in range(0, len(paragraph), max_length - overlap):
                    chunks.append(paragraph[i:i + max_length])
                current = ""
            else:
                current = paragraph

        if current:
            chunks.append(current)

        return chunks

    def _merge_llm_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple LLM extraction results into a single payload with validation."""
        merged = self._empty_result()
        seen_experience = set()

        for result in results:
            if not result:
                continue
            name = result.get("name")
            if name and name != "Unknown" and (merged["name"] == "Unknown" or len(name) > len(merged["name"])):
                merged["name"] = name

            for key in ["email", "phone", "location"]:
                if not merged.get(key) and result.get(key):
                    merged[key] = result.get(key)

            summary = result.get("summary")
            if summary and len(summary) > len(merged.get("summary", "")):
                merged["summary"] = summary

            merged["skills"].extend(result.get("skills", []))
            merged["certifications"].extend(result.get("certifications", []))

            for exp in result.get("experience", []):
                exp_key = (
                    exp.get("org", ""),
                    exp.get("role", ""),
                    exp.get("start", ""),
                    exp.get("end", ""),
                )
                if exp_key in seen_experience:
                    continue
                seen_experience.add(exp_key)
                merged["experience"].append(exp)

        # Deduplicate and validate before limiting
        unique_skills = list(set(merged["skills"]))
        merged["skills"] = CVDataValidator.filter_skills(unique_skills)[:50]

        unique_certs = list(set(merged["certifications"]))
        merged["certifications"] = CVDataValidator.filter_certifications(unique_certs)[:20]

        merged["experience"] = merged["experience"][:15]

        logger.info(f"Merged LLM results: {len(merged['skills'])} valid skills, {len(merged['certifications'])} valid certifications")

        return merged

    def _merge_llm_and_regex(self, llm_data: Optional[Dict[str, Any]], regex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM and regex extraction results with validation."""
        if not llm_data:
            # Apply validation to regex data before returning
            regex_data["skills"] = CVDataValidator.filter_skills(regex_data.get("skills", []))
            regex_data["certifications"] = CVDataValidator.filter_certifications(regex_data.get("certifications", []))
            return regex_data

        merged = dict(llm_data)

        if not merged.get("name") or merged.get("name") == "Unknown":
            merged["name"] = regex_data.get("name", "Unknown")

        for key in ["email", "phone", "location"]:
            if not merged.get(key):
                merged[key] = regex_data.get(key)

        if not merged.get("summary"):
            merged["summary"] = regex_data.get("summary", "")

        # Merge skills and apply validation
        all_skills = list(set((merged.get("skills") or []) + (regex_data.get("skills") or [])))
        merged["skills"] = CVDataValidator.filter_skills(all_skills)[:50]

        # Merge certifications and apply validation
        all_certs = list(set((merged.get("certifications") or []) + (regex_data.get("certifications") or [])))
        merged["certifications"] = CVDataValidator.filter_certifications(all_certs)[:20]

        if not merged.get("experience"):
            merged["experience"] = regex_data.get("experience", [])
        else:
            existing_keys = {
                (exp.get("org", ""), exp.get("role", ""), exp.get("start", ""), exp.get("end", ""))
                for exp in merged["experience"]
            }
            for exp in regex_data.get("experience", []):
                exp_key = (
                    exp.get("org", ""),
                    exp.get("role", ""),
                    exp.get("start", ""),
                    exp.get("end", ""),
                )
                if exp_key not in existing_keys:
                    merged["experience"].append(exp)
                    existing_keys.add(exp_key)
            merged["experience"] = merged["experience"][:15]

        merged["education"] = merged.get("education") or regex_data.get("education", [])

        logger.info(f"Merged results: {len(merged['skills'])} skills, {len(merged['certifications'])} certifications (after validation)")

        return merged

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
        """Extract skills from text with validation to filter out personal data"""
        skills = []

        # Look for skills section with more flexible patterns
        match = re.search(
            r"(?i)(?:technical\s+skills?|skills?|core\s+competencies|technologies|expertise|proficiencies)[\s:]*\n(.*?)(?=\n(?:experience|education|certifications?|employment|projects?|personal|passport|nationality)|\Z)",
            text,
            re.DOTALL,
        )
        if match:
            skills_text = match.group(1)
            # Split by common separators
            tokens = re.split(r"[,;•\|\n\t]", skills_text)
            for token in tokens:
                skill = token.strip()
                # Basic filtering before validation
                if skill and 2 < len(skill) < 100:
                    # Apply comprehensive validation
                    if CVDataValidator.is_valid_skill(skill):
                        skills.append(skill.lower())

        # Comprehensive tech keyword search
        tech_keywords_pattern = r"\b(?:" + "|".join([
            # Programming Languages
            "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "go", "golang", "rust", "php", "swift", "kotlin", "scala", "perl", "r",
            # Web Frontend
            "react", "angular", "vue", "svelte", "html", "css", "sass", "scss", "tailwind", "bootstrap", "jquery",
            # Backend/Frameworks
            "node\\.?js", "express", "django", "flask", "fastapi", "spring", "rails", "laravel", "asp\\.net",
            # Databases
            "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch", "oracle", "mssql",
            # Cloud/DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "gitlab", "github", "circleci",
            "ci/cd", "devops", "cloudformation",
            # Data/ML
            "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "spark", "hadoop", "kafka", "airflow",
            # Tools/Other
            "git", "linux", "bash", "powershell", "api", "rest", "graphql", "microservices", "agile", "scrum", "jira"
        ]) + r")\b"

        tech_keywords = re.findall(tech_keywords_pattern, text, re.IGNORECASE)
        # Validate tech keywords too (in case they're part of a larger invalid string)
        validated_keywords = [k.lower() for k in tech_keywords if CVDataValidator.is_valid_skill(k)]
        skills.extend(validated_keywords)

        # Remove duplicates and apply final filtering
        unique_skills = list(set(skills))
        filtered_skills = CVDataValidator.filter_skills(unique_skills)

        logger.info(f"Extracted {len(skills)} skills, filtered down to {len(filtered_skills)} valid skills")

        return filtered_skills[:50]

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experience = []

        # Look for experience section with flexible patterns
        match = re.search(
            r"(?i)(?:professional\s+experience|work\s+experience|experience|employment\s+history|employment|work\s+history|career\s+history)[\s:]*\n(.*?)(?=\n\s*(?:education|certifications?|skills?|projects?)|\Z)",
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
            r"(?i)(?:education|academic\s+background|qualifications?)[\s:]*\n(.*?)(?=\n\s*(?:experience|certifications?|skills?|projects?)|\Z)",
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
        """Extract certifications with validation to filter out personal data"""
        certs = []
        match = re.search(
            r"(?i)(?:certifications?|certificates?|licenses?|accreditations?)[\s:]*\n(.*?)(?=\n(?:experience|education|skills|personal|passport|nationality)|\Z)",
            text,
            re.DOTALL,
        )
        if match:
            cert_text = match.group(1)
            lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
            for line in lines[:20]:  # Increased to 20 to get more candidates
                if len(line) > 3 and len(line) <= 200:
                    # Clean up common prefixes
                    cleaned = re.sub(r"^[-•\*\d+\.)\s]+", "", line).strip()
                    if cleaned:
                        # Apply validation
                        if CVDataValidator.is_valid_certification(cleaned):
                            certs.append(cleaned[:150])

        # Apply final filtering
        filtered_certs = CVDataValidator.filter_certifications(certs)

        logger.info(f"Extracted {len(certs)} certifications, filtered down to {len(filtered_certs)} valid certifications")

        return filtered_certs

    def _extract_name(self, text: str) -> str:
        """Extract candidate name (usually at top of CV)"""
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Try first 10 lines to find a name
        for i, line in enumerate(lines[:10]):
            # Skip likely header/non-name lines
            if len(line) < 3 or len(line) > 60:
                continue
            if "@" in line or "http" in line.lower():
                continue
            if line.isupper() and len(line) > 30:  # Skip all-caps headers
                continue
            if any(word in line.lower() for word in ["resume", "curriculum", "vitae", "cv", "page"]):
                continue

            # Look for name pattern: Capitalized words (2-4 words typical)
            words = line.split()
            if 2 <= len(words) <= 5:
                # Check if words start with capital letters
                if all(word[0].isupper() for word in words if len(word) > 1):
                    return line

        # Fallback: first non-header line
        for line in lines[:5]:
            if len(line) < 50 and not "@" in line and not line.isupper():
                return line

        return "Unknown"

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if match:
            return match.group(0)
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number with improved patterns"""
        # Comprehensive phone number patterns
        patterns = [
            # US formats
            r"\+?1?[\s.-]?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})",  # (123) 456-7890, 123-456-7890, +1-123-456-7890
            # International formats
            r"\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}",  # +XX XXX XXX XXXX
            # Indian format
            r"\+?91[\s.-]?\d{5}[\s.-]?\d{5}",  # +91 XXXXX XXXXX
            # Generic 10-digit
            r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",  # XXX XXX XXXX or XXX-XXX-XXXX
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0).strip()
                # Basic validation: should have at least 10 digits
                digits_only = re.sub(r'\D', '', phone)
                if len(digits_only) >= 10:
                    return phone
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location"""
        # Look for city, state patterns
        match = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2})\b", text)
        if match:
            return match.group(0)
        return None

    def _apply_normalization(self, parsed: dict) -> dict:
        """
        Apply ontology-based normalization to extracted data.
        - Normalizes skills and certifications to canonical forms
        - Detects skills mentioned in full text and experience entries
        - Adds: skills_normalized, certifications_normalized, skills_map, certifications_map
        - Enhances experience entries with skills_normalized and skills_map
        """
        try:
            # Import normalize service (lazy load to avoid circular imports)
            from app.services.normalize import NormalizeService

            # Load ontology (default staffing agent)
            normalize_service = NormalizeService(
                skills_csv="./config/skills.csv",
                aliases_csv="./config/aliases.csv",
                certs_csv="./config/certs.csv"
            )

            # Keep raw extracted lists
            skills_raw = parsed.get("skills", [])
            certs_raw = parsed.get("certifications", [])

            # Normalize skills list
            skills_normalized = normalize_service.normalize_skills(skills_raw)

            # Also detect skills from full text (catches mentions not explicitly listed)
            raw_text = parsed.get("raw_text", "")
            text_skill_matches = normalize_service.find_skills_in_text(raw_text)
            text_skills = {m["canonical"] for m in text_skill_matches}

            # Merge: explicit + detected from text
            all_skills_set = set(skills_normalized) | text_skills
            skills_normalized_final = sorted(all_skills_set)

            # Build skills map (evidence for each skill)
            skills_map = []
            for skill in skills_normalized_final:
                # Find evidence (from raw list or text detection)
                evidence = []
                for raw_skill in skills_raw:
                    if normalize_service._norm(raw_skill) in normalize_service._norm(skill) or \
                       normalize_service.normalize_skill(raw_skill) == skill:
                        evidence.append(f"explicit: '{raw_skill}'")

                for match in text_skill_matches:
                    if match["canonical"] == skill:
                        evidence.append(match["evidence"])

                skills_map.append({
                    "canonical": skill,
                    "confidence": 0.95 if evidence else 0.80,
                    "evidence": "; ".join(evidence[:3]) if evidence else "detected in text"
                })

            # Normalize certifications
            certs_normalized = normalize_service.normalize_certs(certs_raw)

            # Build certs map
            certs_map = []
            for cert in certs_normalized:
                # Find original mention
                raw_match = [c for c in certs_raw if normalize_service.normalize_cert(c) == cert]
                evidence = f"explicit: '{raw_match[0]}'" if raw_match else "normalized"
                certs_map.append({
                    "canonical": cert,
                    "confidence": 0.95,
                    "evidence": evidence
                })

            # Enhance experience entries with per-role skill detection
            experience_enhanced = []
            for exp in parsed.get("experience", []):
                exp_enhanced = normalize_service.normalize_experience_skills(exp)
                experience_enhanced.append(exp_enhanced)

            # Update parsed dict
            parsed["skills_normalized"] = skills_normalized_final
            parsed["certifications_normalized"] = certs_normalized
            parsed["skills_map"] = skills_map
            parsed["certifications_map"] = certs_map
            parsed["experience"] = experience_enhanced

            logger.info(f"Normalization complete: {len(skills_raw)} raw skills → "
                       f"{len(skills_normalized_final)} normalized (including {len(text_skills)} detected from text), "
                       f"{len(certs_raw)} raw certs → {len(certs_normalized)} normalized")

        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            import traceback
            logger.debug(f"Normalization traceback: {traceback.format_exc()}")

            # Fallback: add empty normalized fields
            parsed["skills_normalized"] = parsed.get("skills", [])
            parsed["certifications_normalized"] = parsed.get("certifications", [])
            parsed["skills_map"] = []
            parsed["certifications_map"] = []

        return parsed

    def _empty_result(self) -> dict:
        """Return empty parsed result"""
        return {
            "summary": "",
            "skills": [],
            "skills_normalized": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "certifications_normalized": [],
            "name": "Unknown",
            "email": None,
            "phone": None,
            "location": None,
            "raw_text": "",
        }
