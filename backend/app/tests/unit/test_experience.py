"""Unit tests for experience calculation utilities."""
from app.services.experience import calculate_total_years_experience


def test_calculate_total_years_experience_with_year_ranges():
    exp = [
        {"start": "2018", "end": "2020"},
        {"start": "Jan 2021", "end": "Jan 2023"},
    ]
    years = calculate_total_years_experience(exp)
    assert years is not None
    assert years >= 4.0


def test_calculate_total_years_experience_with_present():
    exp = [{"start": "2022", "end": "Present"}]
    years = calculate_total_years_experience(exp)
    assert years is not None
    assert years >= 3.0


def test_calculate_total_years_experience_with_invalid_values():
    exp = [{"start": None, "end": "2020"}, {"start": "n/a", "end": "n/a"}]
    assert calculate_total_years_experience(exp) is None
