SELECT
    s.retention_priority,
    s.persona_name,
    COUNT(*) AS customers,
    ROUND(AVG(p.churn_probability)::numeric, 3) AS avg_predicted,
    ROUND(AVG(c.churned::int)::numeric, 3) AS actual_churn_rate,
    ROUND(SUM(p.churn_probability * c.monthly_charges * 12)::numeric, 0) AS revenue_at_risk_12m,
    ROUND(
        (SUM(p.churn_probability * c.monthly_charges * 12)
         / SUM(SUM(p.churn_probability * c.monthly_charges * 12)) OVER ())::numeric, 3
    ) AS share_of_total,
    s.revenue_at_risk_12m AS stored_value
FROM customer_segments cs
JOIN segments  s ON s.id = cs.segment_id
JOIN customers c ON c.id = cs.customer_id
JOIN predictions p
     ON p.customer_id = c.id AND p.analysis_run_id = cs.analysis_run_id
WHERE cs.analysis_run_id = :run_id
GROUP BY s.id, s.retention_priority, s.persona_name, s.revenue_at_risk_12m
ORDER BY s.retention_priority;