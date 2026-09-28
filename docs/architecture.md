# Architecture

## Medallion layers

```
Bronze (raw CSV)     data/bronze/encounters.csv
       │
       ▼  pandas clean & validate
Silver (clean CSV)   data/silver/encounters_clean.csv
       │
       ▼  load to PostgreSQL staging.encounters
Gold (warehouse)     marts.fact_daily_occupancy
       │
       ├──► marts.forecast_occupancy (Prophet)
       └──► Streamlit dashboard
```

## Components

| Component | Technology | Role |
|-----------|-----------|------|
| Data generator | Python | Synthetic Synthea-style encounters |
| Extract/clean | pandas | Bronze → silver → staging |
| Warehouse | PostgreSQL + dbt | Star schema marts |
| Orchestration | Airflow | Daily batch at 06:00 |
| Forecasting | Prophet | 7-day occupancy prediction |
| Reporting | Streamlit | Dashboard + capacity alerts |
| CI | GitHub Actions | Unit tests on every push |

## DE → DS handoff

Data engineering delivers `marts.fact_daily_occupancy`.  
Forecasting reads this table only — never raw encounters.  
Dashboard reads marts only.
