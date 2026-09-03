-- Database initialisation for Bed Occupancy Pipeline
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS staging.encounters (
    encounter_id    VARCHAR(64) PRIMARY KEY,
    patient_id      VARCHAR(64) NOT NULL,
    department      VARCHAR(100) NOT NULL,
    admission_date  DATE NOT NULL,
    discharge_date  DATE,
    encounter_type  VARCHAR(50) DEFAULT 'inpatient',
    loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_encounters_admission ON staging.encounters(admission_date);
CREATE INDEX IF NOT EXISTS idx_encounters_department ON staging.encounters(department);

CREATE TABLE IF NOT EXISTS marts.fact_daily_occupancy (
    date_id         DATE NOT NULL,
    department      VARCHAR(100) NOT NULL,
    beds_occupied   INTEGER NOT NULL,
    total_beds      INTEGER NOT NULL,
    occupancy_rate  NUMERIC(5, 4) NOT NULL,
    admissions_count INTEGER DEFAULT 0,
    discharges_count INTEGER DEFAULT 0,
    PRIMARY KEY (date_id, department)
);

CREATE TABLE IF NOT EXISTS marts.forecast_occupancy (
    forecast_date   DATE NOT NULL,
    department      VARCHAR(100) NOT NULL,
    predicted_beds  NUMERIC(10, 2) NOT NULL,
    predicted_rate  NUMERIC(5, 4) NOT NULL,
    model_run_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (forecast_date, department, model_run_at)
);
