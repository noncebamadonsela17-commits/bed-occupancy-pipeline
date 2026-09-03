# Bed Occupancy Forecasting Pipeline

**Author:** Nonceba Mdonsela  
**Type:** Data Engineering — Batch pipeline, warehouse & time-series forecasting

A cloud-ready data engineering pipeline that ingests hospital encounter data, aggregates daily bed occupancy by department in a PostgreSQL warehouse (dbt), orchestrates runs with Airflow, and produces a 7-day occupancy forecast.

---

## Prerequisites — install before you start

> **Full guide:** [docs/INSTALLATION.md](docs/INSTALLATION.md)

| Tool | Required? | Install command (Pop!_OS / Ubuntu) |
|------|-----------|-------------------------------------|
| **Docker** | Yes | `sudo apt install docker.io docker-compose-v2 -y` |
| **Python 3.11+** | Yes | Usually pre-installed — check with `python3 --version` |
| **make** | Yes | `sudo apt install make -y` |
| **Git** | Yes | `sudo apt install git -y` |

After installing Docker, run:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker   # or log out and back in
```

Python packages are installed from `requirements.txt` (pandas, Prophet, Streamlit, dbt, etc.) — see [Installation Guide](docs/INSTALLATION.md).

---

## Quick start

```bash
# 1. Go to project
cd ~/Downloads/data\ en\ cloud\ project/bed-occupancy-pipeline

# 2. Start PostgreSQL (requires Docker — see INSTALLATION.md)
docker compose up -d

# 3. Create virtualenv & install Python packages (first time only)
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Full install (or use staged install if network is slow — see docs/INSTALLATION.md)
pip install --default-timeout=1000 -r requirements.txt

# Slow internet? Install in stages:
# pip install --default-timeout=1000 -r requirements-core.txt
# pip install --default-timeout=1000 -r requirements-dbt.txt
# pip install --default-timeout=1000 -r requirements-dashboard.txt

# 4. Run the pipeline
make pipeline

# 5. Forecast & dashboard (optional)
make forecast
make dashboard

# 6. Run tests
make test
```

---

## Architecture

```
Synthetic encounters (Synthea / generator)
        │
        ▼
  Bronze (raw CSV)  ── pandas extract/clean
        │
        ▼
  PostgreSQL staging
        │
        ▼
  Silver/Gold (dbt) ── fact_daily_occupancy + dimensions
        │
        ▼
  Airflow (daily DAG)
        │
        ├──► Prophet forecast (7 days)
        └──► Streamlit dashboard
```

---

## Tech stack

| Layer | Tool |
|-------|------|
| Data source | Synthetic encounter generator |
| Extract/clean | pandas |
| Storage | PostgreSQL (Docker) |
| Transform | dbt |
| Orchestration | Airflow |
| Forecasting | Prophet |
| Reporting | Streamlit |

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | **What to install & how to set up** |
| [docs/STUDY_NOTES.md](docs/STUDY_NOTES.md) | **Read this first** — pipeline flow in plain language |
| [docs/4_WEEK_COMMIT_PLAN.md](docs/4_WEEK_COMMIT_PLAN.md) | 4-week GitHub commit and push schedule |
| [docs/architecture.md](docs/architecture.md) | System architecture |
| [docs/data-model.md](docs/data-model.md) | Warehouse data model |
| [docs/runbook.md](docs/runbook.md) | How to run & troubleshoot |

---

## Project structure

```
bed-occupancy-pipeline/
├── scripts/          # Synthetic data generation
├── ingest/           # Extract & load to staging
├── dbt/              # Warehouse models & tests
├── airflow/dags/     # Orchestration
├── forecast/         # 7-day occupancy forecast
├── dashboard/        # Streamlit reporting
├── tests/            # Unit tests
└── docs/             # Documentation & commit plan
```

---

## Occupancy calculation

For department `D` on date `T`:

```
beds_occupied = count(encounters where admit_date <= T
                      and (discharge_date is null or discharge_date > T))
occupancy_rate = beds_occupied / total_beds
```

---

## Explaining this project

Start with [docs/STUDY_NOTES.md](docs/STUDY_NOTES.md). Learn the occupancy rule and the bronze → gold flow by heart before an interview.

## License

Educational portfolio project — synthetic data only.
