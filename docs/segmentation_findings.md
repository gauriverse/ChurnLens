# Customer segmentation findings (Telco dataset)

## Method

- K-Means with k = 5 on standardized behaviour features: tenure, monthly charges, number of add-on services, contract length in months, DSL flag, fiber flag.
- The churn label and the model's probability were NOT used to build the segments. Churn rates below are measured afterwards.
- k choice: silhouette 0.438 (k=4), 0.469 (k=5), 0.482 (k=6). Stability across 5 random seeds was perfect (ARI 1.000) for k = 2 to 6, so it did not separate the options. k = 5 was chosen for interpretability: k = 4 merged the long-tenured fiber and DSL groups, and k = 6 only split the no-internet group into two low-risk halves.
- Silhouette values are inflated by binary and three-valued features and by the tight no-internet group. The segments are stable summaries, not natural boundaries in the data.

## Segments

| Priority | Persona (named by rule from cluster averages) | Customers | Churn rate | Avg monthly | Share of churned monthly revenue (historical) | Share of 12-month revenue at risk (model) | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Newer fiber, month-to-month | 1,932 | 56.3% | $85.06 | 66.6% | 66.5% | High |
| 2 | Long-tenured fiber, longer contracts | 1,164 | 18.0% | $102.18 | 15.5% | 15.4% | Medium |
| 3 | Newer DSL, short contracts | 1,401 | 29.1% | $50.21 | 13.7% | 14.4% | Medium |
| 4 | Long-tenured DSL, longer contracts | 1,020 | 5.0% | $68.94 | 2.5% | 2.0% | Low |
| 5 | No-internet customers | 1,526 | 7.4% | $21.08 | 1.7% | 1.6% | Low |

## Findings

1. Newer fiber month-to-month customers are 27% of the base but account for about two-thirds of churned revenue.
2. Long-tenured fiber customers churn less than newer DSL customers (18% vs 29%) but spend about twice as much, so they carry a larger share of revenue at risk (15.4% vs 14.4%). Ranking by churn rate alone would reverse this.
3. Long-tenured DSL and no-internet customers are low risk and low priority.
4. Historical and model-based revenue shares agree within about 0.7 percentage points. This is partly expected because the probabilities are calibrated to the observed churn rate.

## Limitations

- Example labels from the project brief such as "price-sensitive" and "low-engagement" are not used: the data has no price-sensitivity or usage measure, so those names would be guesses.
- Segments describe association with churn, not causes.
- Revenue at risk = churn probability x monthly charge x 12 months. The 12-month horizon is an assumption, and the figure is revenue, not profit.
- Priority tiers (High at 30% or more of revenue at risk, Medium at 10% or more) are display cutoffs chosen by the author, not statistical thresholds.
- Clustering used all 7,043 customers because no label was involved. The probabilities used for revenue at risk are out-of-sample (out-of-fold for training customers, held-out for test customers).
- K-Means with binary features is an approximation, and new data may need the segmentation retrained.
