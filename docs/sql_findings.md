# SQL checks on the loaded database (analysis run 2, Telco dataset)

## Calibration by probability band (out-of-sample predictions)

| Band | Customers | Avg predicted | Actual churn | Gap (predicted - actual) |
| --- | --- | --- | --- | --- |
| 0.0-0.2 | 3,620 | 0.069 | 0.071 | -0.002 |
| 0.2-0.4 | 1,302 | 0.291 | 0.283 | +0.008 |
| 0.4-0.6 | 1,131 | 0.499 | 0.473 | +0.026 |
| 0.6-0.8 | 952 | 0.685 | 0.707 | -0.021 |
| 0.8-1.0 | 38 | 0.816 | 0.947 | -0.131 |

- Bands with more than 900 customers are within about 2 standard errors of perfect calibration.
- The top band has only 38 customers (about 36 churned). An approximate 95% interval for its true churn rate is 0.83 to 0.98, so the model may understate risk above 0.8, but the sample is too small to conclude. The direction is conservative for ranking.
- Limitation: this check combines out-of-fold predictions (training customers) and held-out predictions (test customers). The calibration method was chosen using the training folds, so the held-out part is the cleanest evidence.

## Cross-check of revenue at risk

Recomputed in SQL from the raw tables, each segment matches the stored value within $1 and the shares match the segmentation findings (newer fiber month-to-month 66.5%).

## Churn by contract and tenure

- Month-to-month churn falls with tenure (55.2% at 0-6 months to 26.0% at 49-72) but stays far above two-year contracts at the same tenure (3.3%).
- Contract and tenure overlap: 36.5% of month-to-month customers have 0-6 months of tenure, versus 74.5% of two-year customers with 49+ months.
- Two-year buckets with 0% churn have only 29, 39 and 90 customers; 0 of 29 is compatible with a true rate up to about 10%.
- One-year churn is roughly flat (8-13%) across tenure; small buckets make this noisy.
