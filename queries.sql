-- queries.sql - the analysis. Run with: python3 run_queries.py
-- Each query answers one plain-English question about the demo data.

-- Q1: Attendance rate per clinic (which clinic has the most no-shows?)
-- name: attendance_by_clinic
SELECT clinic,
       COUNT(*) AS appointments,
       ROUND(100.0 * SUM(attended) / COUNT(*), 1) AS attendance_pct
FROM appointments
GROUP BY clinic
ORDER BY attendance_pct DESC;

-- Q2: Average days waited per appointment reason, longest first
-- name: wait_by_reason
SELECT reason,
       COUNT(*) AS appointments,
       ROUND(AVG(days_waited), 1) AS avg_days_waited
FROM appointments
GROUP BY reason
ORDER BY avg_days_waited DESC;

-- Q3: Monthly appointment volume with a 3-month rolling average (window function)
-- name: monthly_volume
SELECT month,
       appointments,
       ROUND(AVG(appointments) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS rolling_3mo_avg
FROM (
    SELECT substr(appointment_date, 1, 7) AS month, COUNT(*) AS appointments
    FROM appointments
    GROUP BY month
) t
ORDER BY month;

-- Q4: No-show rate by patient age band (join across tables)
-- name: no_show_by_age_band
SELECT p.age_band,
       COUNT(*) AS appointments,
       ROUND(100.0 * (COUNT(*) - SUM(a.attended)) / COUNT(*), 1) AS no_show_pct
FROM appointments a
JOIN patients p ON p.patient_id = a.patient_id
GROUP BY p.age_band
ORDER BY p.age_band;

-- Q5: The 10 patients with the most missed appointments
-- name: top_no_shows
SELECT p.patient_id, p.age_band, p.registered_clinic,
       COUNT(*) AS missed
FROM appointments a
JOIN patients p ON p.patient_id = a.patient_id
WHERE a.attended = 0
GROUP BY p.patient_id
ORDER BY missed DESC, p.patient_id
LIMIT 10;
