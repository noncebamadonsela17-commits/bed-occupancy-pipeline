# Study Notes — Bed Occupancy Pipeline

**Read this first** if you need to explain the project in an interview, a class, or to yourself.

Author: Nonceba Mdonsela  
Purpose: Understand *what* the pipeline does, *why* each layer exists, and *how* data moves from raw encounters to a 7-day forecast.

---

## 1. The problem in one sentence

Hospitals need to know **how full each ward is today**, and **whether they will run out of beds in the next week**.

This project answers that with a **batch data engineering pipeline**:

1. Take hospital stay records (admissions and discharges).
2. Count how many patients occupy a bed in each department **on each day**.
3. Store that in a warehouse.
4. Forecast the next **7 days**.
5. Show it on a dashboard with a warning if occupancy is predicted above 90%.

The data is **synthetic** (fake). Never use real patient records in this repo.

---

## 2. Words you will use a lot

| Word | Meaning in this project |
|------|-------------------------|
| **Encounter** | One hospital stay: a patient is admitted, then discharged (or still in). |
| **Department** | A ward: Emergency, ICU, General Medicine, Surgery, Maternity, Paediatrics. |
| **Occupancy** | How many beds are in use in a department on a given date. |
| **Occupancy rate** | `beds occupied ÷ total beds` (a number between 0 and 1). |
| **Bronze / silver / gold** | Medallion layers: raw → cleaned → analytics-ready. |
| **Staging** | Postgres schema that holds cleaned encounters before they become facts. |
| **Marts** | Postgres schema for tables the dashboard and forecast actually use. |
| **Fact table** | One row per *thing you measure*. Here: one row per **department per day**. |
| **Grain** | What one row represents. Grain of the fact table = department + date. |
| **Batch** | Process a whole day’s (or history’s) data at once, not event-by-event. |
| **Orchestration** | Airflow runs the steps in order, on a schedule. |
| **dbt** | SQL transformations in git, with tests. Warehouse modelling tool. |

---

## 3. The flow — follow the data

Read this section slowly. This **is** the project.

```
  scripts/generate_synthetic_encounters.py
              │
              ▼
  data/bronze/encounters.csv          ← BRONZE (raw, messy-capable)
              │
              ▼  ingest/load_staging.py  (pandas clean)
              │
              ├──► data/silver/encounters_clean.csv     ← SILVER (file)
              └──► staging.encounters  (PostgreSQL)     ← SILVER (database)
                          │
                          ▼  ingest/compute_occupancy.py  (pandas)
                          │
                          ├──► data/gold/fact_daily_occupancy.csv
                          └──► marts.fact_daily_occupancy   ← GOLD
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
         forecast/run_forecast.py              dashboard/app.py
         (Prophet, 7 days)                     (Streamlit)
                    │
                    ▼
         marts.forecast_occupancy
         forecast/output/forecast_7d.csv
```

**Airflow** (`airflow/dags/bed_occupancy_daily.py`) runs the same chain every day at 06:00:

`generate data → load staging → compute occupancy → dbt run → forecast`

You can also run it by hand with `make pipeline` then `make forecast`.

---

## 4. Walk through one patient (the occupancy idea)

This is the most important logic in the whole project. If you can explain this, you understand the pipeline.

Imagine ICU has **20 beds**. Two patients:

| Patient | Admitted | Discharged |
|---------|----------|------------|
| A | 1 Jan | 5 Jan |
| B | 3 Jan | still in (null) |

**Rule:** a patient occupies a bed on date **T** if:

- they were admitted **on or before T**, and
- they have **not yet been discharged** on T  
  (discharge is null, **or** discharge date is **after** T)

So:

| Date | Occupied beds | Why |
|------|---------------|-----|
| 1 Jan | 1 | Only A |
| 2 Jan | 1 | Only A |
| 3 Jan | 2 | A and B |
| 4 Jan | 2 | A and B |
| 5 Jan | 1 | A left on the 5th, B still in |

That is why the code uses:

```text
admission_date <= T
AND (discharge_date IS NULL OR discharge_date > T)
```

**Occupancy rate** for ICU on 3 Jan = `2 / 20 = 0.10` (10%).

This same formula lives in two places (on purpose — pandas for the local pipeline, SQL for the warehouse):

- Python: `ingest/compute_occupancy.py` → `compute_daily_occupancy()`
- SQL: `dbt/models/marts/fact_daily_occupancy.sql`

ADR `docs/adr/002-occupancy-calculation.md` records this decision.

---

## 5. What each folder does

### `scripts/` — create the source

`generate_synthetic_encounters.py` writes **8,000** fake encounters to bronze.

- Six departments, each with a fixed bed count.
- Dates from 2023-01-01 to 2025-12-31.
- Length of stay is a random “around 5 days” (Gaussian).
- If discharge would fall after 2025-12-31, discharge is left empty (still admitted).

This stands in for a real hospital extract (or Synthea). Safe for GitHub.

### `ingest/` — extract, clean, load, aggregate

| File | Job |
|------|-----|
| `db_config.py` | Postgres URL. Default host `localhost`, port **5433**, db `hospital_dw`. |
| `load_staging.py` | Bronze CSV → clean → silver CSV → `staging.encounters`. |
| `compute_occupancy.py` | Read staging → daily occupancy → gold CSV → `marts.fact_daily_occupancy`. |

**Cleaning rules** (`load_staging.py`):

- Parse dates; drop rows missing id, patient, department, or admission.
- Keep only the six valid department names.
- If discharge is **before** admission, wipe the discharge (treat as invalid).
- Drop admissions after 2025-12-31.

Then it **truncates** `staging.encounters` and reloads. Full refresh, not incremental.

### `sql/init.sql` — warehouse empty shell

Docker runs this once when the Postgres container is first created.

- Schema `staging` + table `encounters`
- Schema `marts` + tables `fact_daily_occupancy` and `forecast_occupancy`

Indexes on admission date and department speed filters.

### `dbt/` — same occupancy logic, in SQL, with tests

dbt does **not** replace pandas in `make pipeline`. It is the **warehouse modelling** layer:

- `stg_encounters` — a view over `staging.encounters` (light rename/select).
- `fact_daily_occupancy` — builds a **date spine** (every day × every department), left-joins encounters, counts occupied beds.

Tests:

- unique / not_null on key columns (`models/schema.yml`)
- occupancy_rate must be between 0 and 1 (`tests/assert_occupancy_rate_valid.sql`)

`profiles.yml` (copied from `profiles.yml.example`) has the DB password. **Never commit** the real `profiles.yml`.

### `airflow/` — run the steps in order

DAG id: `bed_occupancy_daily`  
Schedule: `0 6 * * *` (06:00 every day)  
`catchup=False` so it does not backfill years of history on first start.

Tasks are `BashOperator`s that `cd` into the project and run the same Python/dbt commands you run with Make.

### `forecast/` — 7-day prediction

Prophet needs two columns: `ds` (date) and `y` (value). Here `y` is `beds_occupied`.

The script currently forecasts the **first 3 departments** (comment in code: start small, then extend). That is a talking point: you know it is a limitation and how you would finish it (loop all departments).

Output goes to CSV **and** `marts.forecast_occupancy`.

### `dashboard/` — what a manager would look at

Streamlit app:

- Department dropdown
- Current beds, rate, total beds
- Line chart of occupancy rate
- 7-day forecast table
- **Warning** if any predicted rate > 0.9

If Postgres is down, it can fall back to the forecast CSV.

### `tests/` — prove the occupancy rule

`test_occupancy_logic.py` uses the two-patient ICU example:

- rates always between 0 and 1
- on 3 Jan, ICU occupied beds = 2
- ICU capacity is 20

### `.github/workflows/ci.yml`

On push/PR to `main`: install Python 3.11, run pytest.

---

## 6. How you actually run it

```bash
docker compose up -d          # Postgres on port 5433
source .venv/bin/activate
make pipeline                 # data → ingest → aggregate
make forecast                 # Prophet
make dashboard                # http://localhost:8501
make test
```

`make pipeline` is three targets: `data`, `ingest`, `aggregate`.

Postgres is **not** on 5432. The compose file maps **5433:5432** so it does not fight a local Postgres install.

---

## 7. Two ways occupancy is computed (interview question)

**Question:** “Why pandas *and* dbt?”

**Answer you can give:**

> The pandas path (`compute_occupancy.py`) is the working local pipeline: generate, clean, aggregate, load gold. It is easy to test with pytest.
>
> The dbt path is how I would model the same grain in a warehouse: a date spine, SQL tests, and models in git. Airflow runs dbt after the pandas load so the warehouse models stay in the orchestration graph.
>
> In a larger team, pandas ingest would land staging, and dbt would own all marts. I kept both to show extract/load *and* warehouse transform.

---

## 8. Why batch, not streaming?

See `docs/adr/001-batch-vs-streaming.md`.

Bed meetings are daily. Historical encounters do not need second-level latency. Batch is simpler to test and to demo. Airflow at 06:00 matches a morning census.

---

## 9. Data model (what lives in Postgres)

**staging.encounters** — one row per stay.

**marts.fact_daily_occupancy** — one row per department per day:

| Column | Meaning |
|--------|---------|
| date_id | The calendar day |
| department | Ward name |
| beds_occupied | Census count that day |
| total_beds | Capacity (fixed per department) |
| occupancy_rate | occupied / capacity, capped at 1 in pandas |
| admissions_count | Arrivals that day (pandas fact; dbt model currently focuses on occupied + rate) |
| discharges_count | Leavers that day |

**marts.forecast_occupancy** — predicted beds and rate, plus `model_run_at` so reruns do not overwrite history.

Department capacities:

| Department | Beds |
|------------|------|
| Emergency | 40 |
| ICU | 20 |
| General Medicine | 80 |
| Surgery | 50 |
| Maternity | 30 |
| Paediatrics | 35 |

---

## 10. File map (cheat sheet)

| Path | Layer |
|------|--------|
| `scripts/generate_synthetic_encounters.py` | Source |
| `data/bronze/` | Bronze |
| `ingest/load_staging.py` | Bronze → silver + staging |
| `data/silver/` | Silver files |
| `sql/init.sql` | DDL |
| `ingest/compute_occupancy.py` | Staging → gold |
| `data/gold/` | Gold files |
| `dbt/models/` | Warehouse SQL |
| `airflow/dags/bed_occupancy_daily.py` | Orchestration |
| `forecast/run_forecast.py` | Forecast |
| `dashboard/app.py` | Reporting |
| `tests/test_occupancy_logic.py` | Unit tests |
| `docker-compose.yml` | Postgres 16 |
| `Makefile` | One-command runs |

CSV files under `data/` are gitignored. Only `.gitkeep` is committed. That is correct for a portfolio: you generate data locally; you never publish “patient” files.

---

## 11. Elevator pitch (memorise this)

> I built a batch data engineering pipeline that ingests synthetic hospital encounter data, cleans it into a silver layer, loads PostgreSQL staging, and aggregates daily bed occupancy by department into a gold fact table. I modelled the same grain in dbt with tests, orchestrated the run with an Airflow DAG, added GitHub Actions CI, and delivered a 7-day Prophet forecast on a Streamlit dashboard with a 90% capacity alert.

---

## 12. Questions you should be ready for

**What is the grain of the fact table?**  
One row per department per day.

**How do you handle a patient still in hospital?**  
`discharge_date` is null, so they count as occupied on every day from admission through the end of the date range.

**Why port 5433?**  
Host port 5433 maps to container 5432 so a local Postgres on 5432 is left alone.

**Does the dashboard read bronze?**  
No. Engineering hands off `marts.fact_daily_occupancy` (and forecast). That is the DE → analytics contract.

**What would you improve next?**

- Forecast all six departments, not three.
- Incremental loads instead of `TRUNCATE`.
- Align pandas fact columns (admissions/discharges) with the dbt model.
- Great Expectations or a real Synthea extract.
- Deploy Postgres + Airflow instead of local Docker.

**What must never go to GitHub?**  
`.venv/`, generated CSVs, `dbt/profiles.yml`, real patient data, passwords.

---

## 13. How to practise explaining it

Say this out loud, pointing at folders:

1. “Generator writes bronze CSV.”
2. “Pandas cleans to silver and staging.”
3. “Occupancy is a daily census per ward.”
4. “Gold fact table is what forecasting is allowed to see.”
5. “Airflow is the schedule; dbt is the SQL warehouse layer; Streamlit is the product.”

If you can do that without looking at notes, you know the project.
