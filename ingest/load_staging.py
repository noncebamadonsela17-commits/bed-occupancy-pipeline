#!/usr/bin/env python3
"""Extract bronze CSV, clean records, load into PostgreSQL staging."""
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
from db_config import connection_string

BRONZE = Path(__file__).parent.parent / "data" / "bronze" / "encounters.csv"
SILVER = Path(__file__).parent.parent / "data" / "silver" / "encounters_clean.csv"

VALID_DEPARTMENTS = {
    "Emergency", "ICU", "General Medicine", "Surgery", "Maternity", "Paediatrics"
}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["admission_date"] = pd.to_datetime(df["admission_date"], errors="coerce")
    df["discharge_date"] = pd.to_datetime(df["discharge_date"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["encounter_id", "patient_id", "department", "admission_date"])
    df = df[df["department"].isin(VALID_DEPARTMENTS)]

    # Discharge must be on or after admission
    mask = df["discharge_date"].notna() & (df["discharge_date"] < df["admission_date"])
    df.loc[mask, "discharge_date"] = pd.NaT

    # No future dates beyond data range
    max_date = pd.Timestamp("2025-12-31")
    df = df[df["admission_date"] <= max_date]

    df["admission_date"] = df["admission_date"].dt.date
    df["discharge_date"] = df["discharge_date"].apply(
        lambda x: x.date() if pd.notna(x) else None
    )
    return df


def load_to_staging(df: pd.DataFrame) -> int:
    engine = create_engine(connection_string())
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE staging.encounters"))
        df.to_sql(
            "encounters",
            conn,
            schema="staging",
            if_exists="append",
            index=False,
            method="multi",
        )
    return len(df)


def main():
    if not BRONZE.exists():
        raise FileNotFoundError(f"Bronze file not found: {BRONZE}. Run: make data")

    raw = pd.read_csv(BRONZE)
    print(f"Read {len(raw)} raw encounters")

    cleaned = clean(raw)
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(SILVER, index=False)
    print(f"Cleaned -> {len(cleaned)} records saved to silver")

    loaded = load_to_staging(cleaned)
    print(f"Loaded {loaded} records into staging.encounters")


if __name__ == "__main__":
    main()
