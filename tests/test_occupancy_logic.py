"""Tests for occupancy calculation logic."""
import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "ingest"))
from compute_occupancy import compute_daily_occupancy, DEPARTMENT_BEDS


@pytest.fixture
def sample_encounters():
    return pd.DataFrame([
        {"encounter_id": "1", "department": "ICU", "admission_date": "2025-01-01", "discharge_date": "2025-01-05"},
        {"encounter_id": "2", "department": "ICU", "admission_date": "2025-01-03", "discharge_date": None},
    ])


def test_occupancy_rate_between_zero_and_one(sample_encounters):
    fact = compute_daily_occupancy(sample_encounters)
    assert (fact["occupancy_rate"] >= 0).all()
    assert (fact["occupancy_rate"] <= 1).all()


def test_icu_occupied_on_jan_3(sample_encounters):
    fact = compute_daily_occupancy(sample_encounters)
    row = fact[(fact["department"] == "ICU") & (fact["date_id"] == pd.Timestamp("2025-01-03").date())]
    assert row.iloc[0]["beds_occupied"] == 2


def test_department_beds_defined():
    assert "ICU" in DEPARTMENT_BEDS
    assert DEPARTMENT_BEDS["ICU"] == 20
