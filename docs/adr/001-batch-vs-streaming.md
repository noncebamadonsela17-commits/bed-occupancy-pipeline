# ADR 001: Batch vs Streaming

## Status
Accepted

## Context
Hospital bed occupancy could be computed in real-time or batch.

## Decision
Use **daily batch** processing scheduled at 06:00.

## Rationale
- Historical encounter data does not require sub-minute latency
- Batch is simpler to implement, test, and demonstrate for portfolio
- Aligns with standard hospital reporting cycles (daily bed meetings)
