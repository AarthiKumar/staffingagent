"""Experience date parsing and total experience calculation helpers."""
from __future__ import annotations

from datetime import datetime, date
import re
from typing import Any, Dict, Iterable, Optional, Tuple


_MONTH_PATTERNS = [
    "%b %Y",   # Jan 2020
    "%B %Y",   # January 2020
    "%m/%Y",   # 01/2020
    "%Y-%m",   # 2020-01
    "%Y",      # 2020
]

_PRESENT_VALUES = {"present", "current", "now", "ongoing", "till date", "till now"}


def _parse_date_value(value: Any, default_to_end_of_year: bool = False) -> Optional[date]:
    """Parse a flexible date string into a date."""
    if value is None:
        return None
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    text_lower = text.lower()
    if text_lower in _PRESENT_VALUES:
        return datetime.utcnow().date()

    # Normalize separators to simplify parsing attempts.
    normalized = re.sub(r"[\.\-]", "/", text)

    for pattern in _MONTH_PATTERNS:
        try:
            parsed = datetime.strptime(text, pattern)
            if pattern == "%Y" and default_to_end_of_year:
                return date(parsed.year, 12, 31)
            return date(parsed.year, parsed.month, 1)
        except ValueError:
            pass
        try:
            parsed = datetime.strptime(normalized, pattern.replace("-", "/"))
            if pattern == "%Y" and default_to_end_of_year:
                return date(parsed.year, 12, 31)
            return date(parsed.year, parsed.month, 1)
        except ValueError:
            pass

    # Last-resort year extraction.
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        year = int(year_match.group(0))
        if default_to_end_of_year:
            return date(year, 12, 31)
        return date(year, 1, 1)

    return None


def _interval_months(start: date, end: date) -> float:
    """Compute duration in months between two dates (inclusive month approximation)."""
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return max(0, float(months))


def calculate_total_years_experience(experience_items: Iterable[Dict[str, Any]]) -> Optional[float]:
    """Calculate total years of experience from extracted experience items."""
    total_months = 0.0

    for item in experience_items or []:
        if not isinstance(item, dict):
            continue

        start = _parse_date_value(item.get("start"))
        end = _parse_date_value(item.get("end"), default_to_end_of_year=True) or datetime.utcnow().date()
        if not start or end < start:
            continue

        total_months += _interval_months(start, end)

    if total_months <= 0:
        return None

    return round(total_months / 12.0, 2)
