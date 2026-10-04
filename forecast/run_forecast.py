#!/usr/bin/env python3
"""Forecast next 7 days of bed occupancy per department using Prophet."""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent / "ingest"))
from db_config import connection_string

OUTPUT_DIR = Path(__file__).parent / "output"
FORECAST_DAYS = 7


def forecast_department(history: pd.DataFrame, department: str) -> pd.DataFrame:
    dept = history[history["department"] == department].copy()
    dept = dept.rename(columns={"date_id": "ds", "beds_occupied": "y"})
    dept["ds"] = pd.to_datetime(dept["ds"])

    model = Prophet(daily_seasonality=True, weekly_seasonality=True)
    model.fit(dept[["ds", "y"]])

    future = model.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = model.predict(future).tail(FORECAST_DAYS)

    total_beds = dept["total_beds"].iloc[0] if "total_beds" in dept.columns else 50
    result = pd.DataFrame({
        "forecast_date": forecast["ds"].dt.date,
        "department": department,
        "predicted_beds": forecast["yhat"].round(1),
        "predicted_rate": (forecast["yhat"] / total_beds).clip(0, 1).round(4),
        "model_run_at": datetime.now(),
    })
    return result


def main():
    engine = create_engine(connection_string())
    history = pd.read_sql(
        "SELECT date_id, department, beds_occupied, total_beds, occupancy_rate "
        "FROM marts.fact_daily_occupancy ORDER BY date_id",
        engine,
    )

    if history.empty:
        print("No occupancy data. Run: make ingest && make aggregate")
        sys.exit(1)

    departments = history["department"].unique()
    # Start with one department, extend to all
    target_depts = list(departments) if len(departments) <= 3 else list(departments)[:3]

    all_forecasts = []
    for dept in target_depts:
        print(f"Forecasting: {dept}")
        fc = forecast_department(history, dept)
        all_forecasts.append(fc)

    result = pd.concat(all_forecasts, ignore_index=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "forecast_7d.csv"
    result.to_csv(out_file, index=False)

    result.to_sql(
        "forecast_occupancy",
        engine,
        schema="marts",
        if_exists="append",
        index=False,
    )
    print(f"Forecast saved -> {out_file} ({len(result)} rows)")


if __name__ == "__main__":
    main()
