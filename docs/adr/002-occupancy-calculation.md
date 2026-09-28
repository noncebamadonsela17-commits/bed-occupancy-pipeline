# ADR 002: Occupancy Calculation

## Status
Accepted

## Decision
A patient occupies a bed on date T if:
- `admission_date <= T`
- AND (`discharge_date IS NULL` OR `discharge_date > T`)

## Rationale
- Standard hospital census definition
- Handles patients still admitted (null discharge)
- Reproducible and auditable for each department/day
