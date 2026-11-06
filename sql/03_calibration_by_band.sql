WITH scored AS (
    SELECT
        p.churn_probability,
        c.churned::int AS churned,
        LEAST(FLOOR(p.churn_probability * 5), 4)::int AS band
    FROM predictions p
    JOIN customers c ON c.id = p.customer_id
    WHERE p.analysis_run_id = :run_id
)
SELECT
    band,
    ROUND(band * 0.2, 1)       AS from_probability,
    ROUND((band + 1) * 0.2, 1) AS to_probability,
    COUNT(*) AS customers,
    ROUND(AVG(churn_probability)::numeric, 3) AS avg_predicted,
    ROUND(AVG(churned)::numeric, 3)           AS actual_churn_rate,
    ROUND((AVG(churn_probability) - AVG(churned))::numeric, 3) AS gap
FROM scored
GROUP BY band
ORDER BY band;