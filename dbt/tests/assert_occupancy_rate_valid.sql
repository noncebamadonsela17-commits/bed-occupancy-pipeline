select * from {{ ref('fact_daily_occupancy') }}
where occupancy_rate < 0 or occupancy_rate > 1
