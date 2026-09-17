with dates as (
    select generate_series(
        (select min(admission_date) from {{ ref('stg_encounters') }})::date,
        '2025-12-31'::date,
        '1 day'::interval
    )::date as date_id
),

departments as (
    select distinct department,
        case department
            when 'Emergency' then 40
            when 'ICU' then 20
            when 'General Medicine' then 80
            when 'Surgery' then 50
            when 'Maternity' then 30
            when 'Paediatrics' then 35
        end as total_beds
    from {{ ref('stg_encounters') }}
),

spine as (
    select d.date_id, dept.department, dept.total_beds
    from dates d cross join departments dept
),

occupied as (
    select
        s.date_id,
        s.department,
        s.total_beds,
        count(e.encounter_id) as beds_occupied
    from spine s
    left join {{ ref('stg_encounters') }} e
        on e.department = s.department
        and e.admission_date <= s.date_id
        and (e.discharge_date is null or e.discharge_date > s.date_id)
    group by s.date_id, s.department, s.total_beds
)

select
    date_id,
    department,
    beds_occupied,
    total_beds,
    round(beds_occupied::numeric / total_beds, 4) as occupancy_rate
from occupied
