# Pipeline Runbook

> **First time setup?** See [INSTALLATION.md](INSTALLATION.md) for what to install (Docker, Python, etc.)

## Prerequisites check

```bash
docker --version       # Must work
python3 --version      # 3.11+
source .venv/bin/activate  # venv must be active
```

## Start infrastructure

```bash
docker compose up -d
docker compose ps      # confirm postgres is running
```

## Full pipeline run

```bash
source .venv/bin/activate
make pipeline      # data → ingest → aggregate
make forecast      # Prophet 7-day forecast
make dashboard     # Streamlit UI at http://localhost:8501
make test          # unit tests
```

## Backfill (re-run aggregation)

```bash
make data && make ingest && make aggregate
```

## dbt (Week 2)

```bash
cp dbt/profiles.yml.example dbt/profiles.yml
make dbt-run
make dbt-test
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Command 'docker' not found` | Install Docker — see [INSTALLATION.md](INSTALLATION.md) |
| `permission denied` on docker | `sudo usermod -aG docker $USER` then log out/in |
| Cannot connect to Postgres | `docker compose up -d` — check port 5433 |
| Empty fact table | Run `make ingest` first |
| Forecast fails | Need occupancy data — run `make pipeline` first |
| dbt fails | Copy `dbt/profiles.yml.example` to `dbt/profiles.yml` |
| `ModuleNotFoundError` | Activate venv: `source .venv/bin/activate` |
| Dashboard error | Run `make pipeline` before `make dashboard` |

## Airflow

DAG: `bed_occupancy_daily` — scheduled daily at 06:00 UTC
