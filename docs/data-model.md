# Data Model

## Source: staging.encounters

| Column | Type | Description |
|--------|------|-------------|
| encounter_id | VARCHAR | Unique encounter identifier |
| patient_id | VARCHAR | Anonymized patient ID |
| department | VARCHAR | Hospital department |
| admission_date | DATE | Date of admission |
| discharge_date | DATE | Date of discharge (null = still admitted) |

## Fact: marts.fact_daily_occupancy

**Grain:** One row per department per day

| Column | Type | Description |
|--------|------|-------------|
| date_id | DATE | Calendar date |
| department | VARCHAR | Department name |
| beds_occupied | INTEGER | Patients in beds on that date |
| total_beds | INTEGER | Department capacity |
| occupancy_rate | NUMERIC | beds_occupied / total_beds (0–1) |
| admissions_count | INTEGER | Admissions on that date |
| discharges_count | INTEGER | Discharges on that date |

## Occupancy formula

```
beds_occupied(D, T) = COUNT encounters
  WHERE department = D
    AND admission_date <= T
    AND (discharge_date IS NULL OR discharge_date > T)

occupancy_rate = beds_occupied / total_beds
```

## Departments & capacity

| Department | Total beds |
|------------|-----------|
| Emergency | 40 |
| ICU | 20 |
| General Medicine | 80 |
| Surgery | 50 |
| Maternity | 30 |
| Paediatrics | 35 |
