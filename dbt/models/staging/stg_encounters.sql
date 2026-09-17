select
    encounter_id,
    patient_id,
    department,
    admission_date,
    discharge_date,
    encounter_type,
    loaded_at
from {{ source('staging', 'encounters') }}
