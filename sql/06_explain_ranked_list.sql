EXPLAIN (ANALYZE, BUFFERS)
SELECT c.external_customer_id, p.churn_probability
FROM predictions p
JOIN customers c ON c.id = p.customer_id
WHERE p.analysis_run_id = :run_id
ORDER BY p.churn_probability DESC, p.id
LIMIT 25;