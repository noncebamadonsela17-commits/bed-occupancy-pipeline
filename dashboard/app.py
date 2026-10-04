"""Bed Occupancy Forecasting Dashboard — Streamlit."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent / "ingest"))
from db_config import connection_string

st.set_page_config(page_title="Bed Occupancy Forecast", layout="wide")
st.title("Hospital Bed Occupancy — Forecast Dashboard")
st.caption("Nonceba Mdonsela · Data Engineering Portfolio Project")


@st.cache_data
def load_occupancy():
    engine = create_engine(connection_string())
    df = pd.read_sql(
        "SELECT * FROM marts.fact_daily_occupancy ORDER BY date_id",
        engine,
    )
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


@st.cache_data
def load_encounters():
    engine = create_engine(connection_string())
    df = pd.read_sql(
        "SELECT encounter_id, patient_id, department, admission_date, "
        "discharge_date, encounter_type FROM staging.encounters "
        "ORDER BY admission_date DESC LIMIT 200",
        engine,
    )
    return df


@st.cache_data
def load_forecast():
    engine = create_engine(connection_string())
    try:
        return pd.read_sql(
            "SELECT DISTINCT ON (forecast_date, department) * "
            "FROM marts.forecast_occupancy ORDER BY forecast_date, department, model_run_at DESC",
            engine,
        )
    except Exception:
        path = Path(__file__).parent.parent / "forecast" / "output" / "forecast_7d.csv"
        if path.exists():
            return pd.read_csv(path, parse_dates=["forecast_date"])
        return pd.DataFrame()


try:
    occupancy = load_occupancy()
    encounters = load_encounters()
    forecast = load_forecast()
except Exception as e:
    st.error(f"Cannot connect to database. Run: docker compose up -d && make pipeline\n\n{e}")
    st.stop()

departments = sorted(occupancy["department"].unique())
selected = st.sidebar.selectbox("Department", departments)

dept_data = occupancy[occupancy["department"] == selected].sort_values("date_id")
dept_forecast = (
    forecast[forecast["department"] == selected] if not forecast.empty else pd.DataFrame()
)

latest = dept_data.iloc[-1] if not dept_data.empty else None
col1, col2, col3 = st.columns(3)
if latest is not None:
    col1.metric("Latest occupancy", f"{latest['beds_occupied']:.0f} beds")
    col2.metric("Occupancy rate", f"{latest['occupancy_rate'] * 100:.1f}%")
    col3.metric("Ward capacity", f"{latest['total_beds']:.0f} beds")

tab_chart, tab_gold, tab_bronze = st.tabs(
    ["Trend chart", "Daily occupancy (gold)", "Patient stays (bronze / staging)"]
)

with tab_chart:
    st.subheader(f"Occupancy trend — {selected}")
    fig = px.line(
        dept_data,
        x="date_id",
        y="occupancy_rate",
        labels={"date_id": "Date", "occupancy_rate": "Occupancy rate"},
    )
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

    if not dept_forecast.empty:
        st.subheader("7-day forecast")
        fc = dept_forecast.copy()
        fc["Predicted occupancy"] = (fc["predicted_rate"] * 100).round(1).map("{}%".format)
        st.dataframe(
            fc[["forecast_date", "predicted_beds", "Predicted occupancy"]].rename(
                columns={"forecast_date": "Date", "predicted_beds": "Predicted beds"}
            ),
            hide_index=True,
            use_container_width=True,
        )
        if (dept_forecast["predicted_rate"] > 0.9).any():
            st.warning(f"{selected} predicted above 90% capacity in the next 7 days!")
    else:
        st.info("No forecast yet. In a new terminal run: make forecast")

with tab_gold:
    st.subheader(f"How full was {selected} each day?")
    st.caption("This is the gold table: one row per department per day, not per patient.")
    gold = dept_data.sort_values("date_id", ascending=False).copy()
    gold["Occupancy"] = (gold["occupancy_rate"] * 100).round(1).map("{}%".format)
    pretty = gold.rename(
        columns={
            "date_id": "Date",
            "beds_occupied": "Beds used",
            "total_beds": "Capacity",
            "admissions_count": "Admissions",
            "discharges_count": "Discharges",
        }
    )[["Date", "Beds used", "Capacity", "Occupancy", "Admissions", "Discharges"]]
    pretty["Date"] = pretty["Date"].dt.date
    st.dataframe(pretty, hide_index=True, use_container_width=True, height=420)

with tab_bronze:
    st.subheader("Individual hospital stays")
    st.caption("This is staging (cleaned bronze): one row per patient stay.")
    stays = encounters[encounters["department"] == selected].copy()
    if stays.empty:
        stays = encounters.copy()
    stays = stays.rename(
        columns={
            "encounter_id": "Stay ID",
            "patient_id": "Patient ID",
            "department": "Department",
            "admission_date": "Admitted",
            "discharge_date": "Discharged",
            "encounter_type": "Type",
        }
    )
    st.dataframe(stays, hide_index=True, use_container_width=True, height=420)
    st.caption("Showing the 200 most recent stays in staging. Empty Discharged means still admitted.")
