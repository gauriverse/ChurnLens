WITH base AS (
    SELECT
        contract,
        CASE WHEN tenure <= 6  THEN 1
             WHEN tenure <= 12 THEN 2
             WHEN tenure <= 24 THEN 3
             WHEN tenure <= 48 THEN 4
             ELSE 5 END AS bucket_order,
        CASE WHEN tenure <= 6  THEN '0-6'
             WHEN tenure <= 12 THEN '7-12'
             WHEN tenure <= 24 THEN '13-24'
             WHEN tenure <= 48 THEN '25-48'
             ELSE '49-72' END AS tenure_bucket,
        churned
    FROM customers
    WHERE dataset_id = :dataset_id
),
agg AS (
    SELECT contract, tenure_bucket, bucket_order,
           COUNT(*) AS customers,
           ROUND(AVG(churned::int)::numeric, 3) AS churn_rate
    FROM base
    GROUP BY contract, tenure_bucket, bucket_order
)
SELECT
    contract,
    tenure_bucket,
    customers,
    churn_rate,
    ROUND(customers::numeric / SUM(customers) OVER (PARTITION BY contract), 3) AS share_of_contract,
    RANK() OVER (ORDER BY churn_rate DESC) AS risk_rank
FROM agg
ORDER BY contract, bucket_order;