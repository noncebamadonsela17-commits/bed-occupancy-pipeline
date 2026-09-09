#!/usr/bin/env python3
"""
Generate synthetic hospital encounter data (Synthea-style).
Safe for portfolio use — no real patient data.
"""
import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "data" / "bronze" / "encounters.csv"

DEPARTMENTS = {
    "Emergency": 40,
    "ICU": 20,
    "General Medicine": 80,
    "Surgery": 50,
    "Maternity": 30,
    "Paediatrics": 35,
}

ENCOUNTER_COUNT = 8000
START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_encounters(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        dept = random.choices(
            list(DEPARTMENTS.keys()),
            weights=[40, 15, 25, 20, 15, 12],
            k=1,
        )[0]
        admit = random_date(START_DATE, END_DATE - timedelta(days=30))
        length_of_stay = max(1, int(random.gauss(5, 4)))
        discharge = admit + timedelta(days=length_of_stay)
        if discharge > END_DATE:
            discharge = None  # still admitted

        rows.append({
            "encounter_id": str(uuid.uuid4())[:12],
            "patient_id": str(uuid.uuid4())[:10],
            "department": dept,
            "admission_date": admit.isoformat(),
            "discharge_date": discharge.isoformat() if discharge else "",
            "encounter_type": random.choice(["inpatient", "inpatient", "inpatient", "observation"]),
        })
    return rows


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_encounters(ENCOUNTER_COUNT)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} encounters -> {OUTPUT}")


if __name__ == "__main__":
    main()
