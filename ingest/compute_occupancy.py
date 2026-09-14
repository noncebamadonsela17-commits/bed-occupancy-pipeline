#!/usr/bin/env python3
"""
Compute daily bed occupancy per department and load into marts.fact_daily_occupancy.
"""
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).parent))
from db_config import connection_string

DEPARTMENT_BEDS = {
    "Emergency": 40,
    "ICU": 20,
    "General Medicine": 80,
    "Surgery": 50,
    "Maternity": 30,
    "Paediatrics": 35,
}


def compute_daily_occupancy(encounters: pd.DataFrame) -> pd.DataFrame:
    encounters = encounters.copy()
    encounters["admission_date"] = pd.to_datetime(encounters["admission_date"])
    encounters["discharge_date"] = pd.to_datetime(encounters["discharge_date"])

    min_date = encounters["admission_date"].min().date()
    max_date = pd.Timestamp("2025-12-31").date()

    rows = []
    current = min_date
    while current <= max_date:
        for dept, total_beds in DEPARTMENT_BEDS.items():
            dept_enc = encounters[encounters["department"] == dept]
            occupied = dept_enc[
                (dept_enc["admission_date"].dt.date <= current)
                & (
                    dept_enc["discharge_date"].isna()
                    | (dept_enc["discharge_date"].dt.date > current)
                )
            ]
            beds_occupied = len(occupied)
            admissions = len(dept_enc[dept_enc["admission_date"].dt.date == current])
            discharges = len(
                dept_enc[
                    dept_enc["discharge_date"].notna()
                    & (dept_enc["discharge_date"].dt.date == current)
                ]
            )
            rows.append({
                "date_id": current,
                "department": dept,
                "beds_occupied": beds_occupied,
                "total_beds": total_beds,
                "occupancy_rate": round(min(beds_occupied / total_beds, 1.0), 4),
                "admissions_count": admissions,
                "discharges_count": discharges,
            })
        current += timedelta(days=1)

    return pd.DataFrame(rows)


def load_fact_table(df: pd.DataFrame) -> int:
    engine = create_engine(connection_string())
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE marts.fact_daily_occupancy"))
        df.to_sql(
            "fact_daily_occupancy",
            conn,
            schema="marts",
            if_exists="append",
            index=False,
            method="multi",
        )
    return len(df)


def main():
    engine = create_engine(connection_string())
    encounters = pd.read_sql("SELECT * FROM staging.encounters", engine)
    print(f"Computing occupancy from {len(encounters)} encounters")

    fact = compute_daily_occupancy(encounters)
    gold_path = Path(__file__).parent.parent / "data" / "gold" / "fact_daily_occupancy.csv"
    gold_path.parent.mkdir(parents=True, exist_ok=True)
    fact.to_csv(gold_path, index=False)

    loaded = load_fact_table(fact)
    print(f"Loaded {loaded} rows into marts.fact_daily_occupancy")


if __name__ == "__main__":
    main()
