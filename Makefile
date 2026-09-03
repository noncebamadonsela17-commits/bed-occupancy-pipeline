.PHONY: setup data ingest aggregate forecast dashboard pipeline pipeline-all test dbt-run dbt-test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

data:
	python scripts/generate_synthetic_encounters.py

ingest:
	python ingest/load_staging.py

aggregate:
	python ingest/compute_occupancy.py

forecast:
	python forecast/run_forecast.py

dashboard:
	streamlit run dashboard/app.py

pipeline: data ingest aggregate

pipeline-all: data ingest aggregate forecast

test:
	pytest tests/ -v

dbt-run:
	cd dbt && dbt run --profiles-dir .

dbt-test:
	cd dbt && dbt test --profiles-dir .
