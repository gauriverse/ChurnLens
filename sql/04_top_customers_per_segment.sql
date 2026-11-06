WITH ranked AS (
    SELECT
        s.persona_name,
        c.external_customer_id,
        p.churn_probability,
        c.monthly_charges,
        r.expected_value,
        r.priority_rank,
        ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY r.expected_value DESC) AS rn
    FROM retention_recommendations r
    JOIN customers c ON c.id = r.customer_id
    JOIN predictions p
         ON p.customer_id = c.id AND p.analysis_run_id = r.analysis_run_id
    JOIN customer_segments cs
         ON cs.customer_id = c.id AND cs.analysis_run_id = r.analysis_run_id
    JOIN segments s ON s.id = cs.segment_id
    WHERE r.analysis_run_id = :run_id
)
SELECT
    persona_name,
    rn AS position_in_segment,
    external_customer_id,
    ROUND(churn_probability::numeric, 3) AS probability,
    monthly_charges,
    expected_value,
    priority_rank AS overall_rank
FROM ranked
WHERE rn <= 3
ORDER BY persona_name, rn;