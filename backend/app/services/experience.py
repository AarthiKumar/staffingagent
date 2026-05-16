"""Experience date parsing and total experience calculation helpers."""
from __future__ import annotations

from datetime import datetime, date
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


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
    intervals: List[Tuple[date, date]] = []

    for item in experience_items or []:
        if not isinstance(item, dict):
            continue

        start = _parse_date_value(item.get("start"))
        end = _parse_date_value(item.get("end"), default_to_end_of_year=True) or datetime.utcnow().date()
        if not start or end < start:
            continue

        intervals.append((start, end))

    if not intervals:
        return None

    merged = _merge_intervals(intervals)
    total_months = sum(_interval_months(start, end) for start, end in merged)

    if total_months <= 0:
        return None

    return round(total_months / 12.0, 2)


def extract_experience_window(experience_items: Iterable[Dict[str, Any]]) -> Tuple[Optional[date], Optional[date]]:
    """
    Extract overall candidate experience window from parsed start/end dates.
    Returns `(earliest_start, latest_end)`.
    """
    starts: List[date] = []
    ends: List[date] = []

    for item in experience_items or []:
        if not isinstance(item, dict):
            continue
        start = _parse_date_value(item.get("start"))
        end = _parse_date_value(item.get("end"), default_to_end_of_year=True) or datetime.utcnow().date()
        if start and end and end >= start:
            starts.append(start)
            ends.append(end)

    if not starts or not ends:
        return None, None
    return min(starts), max(ends)


def _merge_intervals(intervals: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """Merge overlapping experience date intervals to avoid double-counting."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: item[0])
    merged: List[Tuple[date, date]] = [ordered[0]]

    for current_start, current_end in ordered[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged
