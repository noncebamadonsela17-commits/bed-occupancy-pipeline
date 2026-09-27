"""
Bed Occupancy Pipeline — Daily batch DAG
Nonceba Mdonsela
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "nonceba",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="bed_occupancy_daily",
    default_args=default_args,
    description="Daily bed occupancy aggregation and forecast",
    schedule_interval="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["hospital", "occupancy", "forecast"],
) as dag:

    generate_data = BashOperator(
        task_id="generate_synthetic_data",
        bash_command=f"cd {PROJECT_DIR} && python scripts/generate_synthetic_encounters.py",
    )

    load_staging = BashOperator(
        task_id="load_staging",
        bash_command=f"cd {PROJECT_DIR} && python ingest/load_staging.py",
    )

    compute_occupancy = BashOperator(
        task_id="compute_daily_occupancy",
        bash_command=f"cd {PROJECT_DIR} && python ingest/compute_occupancy.py",
    )

    run_dbt = BashOperator(
        task_id="run_dbt_models",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run --profiles-dir .",
    )

    run_forecast = BashOperator(
        task_id="run_forecast",
        bash_command=f"cd {PROJECT_DIR} && python forecast/run_forecast.py",
    )

    generate_data >> load_staging >> compute_occupancy >> run_dbt >> run_forecast
