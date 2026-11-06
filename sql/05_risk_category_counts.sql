SELECT risk_category,
       COUNT(*) AS customers,
       ROUND(MIN(churn_probability)::numeric, 3) AS min_probability,
       ROUND(MAX(churn_probability)::numeric, 3) AS max_probability
FROM predictions
WHERE analysis_run_id = :run_id
GROUP BY risk_category
ORDER BY min_probability;