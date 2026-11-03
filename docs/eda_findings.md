# EDA findings (Telco dataset, 7,043 customers, 26.5% churn)

1. Contract: month-to-month churn 42.7%, one-year 11.3%, two-year 2.8%. Chi-square p < 1e-250, Cramer's V = 0.41.
2. Tenure: churned customers have a median tenure of 10 months vs. 38 months for retained customers (p = 2.42e-208).
3. Payment method: electronic check users have the highest churn (45.29%), compared to 15.24–19.11% for other methods. Cramer's V = 0.303.
4. Monthly charges: churned customers have a higher median ($79.65) than retained customers ($64.43), p = 3.31e-54.
5. Features with no meaningful relationship: Gender (V = 0.008) and PhoneService (V = 0.011). MultipleLines also has a negligible association (V = 0.040).

Caveats: associations only, not causal. Features overlap, so single-feature rankings are not model importance.