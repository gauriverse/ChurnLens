# Survival analysis findings (Telco dataset)

## Data and setup
- 7,043 customers; 11 customers with tenure 0 were excluded (no observed time), leaving 7,032.
- Duration = tenure in months. Event = Churn (1 = churned, 0 = right-censored, still active when the data was captured).
- This is a single snapshot. There are no calendar dates, so we cannot study how churn changed over time or predict exact churn dates.

## Kaplan-Meier results
- Probability of still being a customer: 84.3% at 12 months, 78.9% at 24 months, 70.9% at 48 months, 59.3% at 72 months.
- Median survival time is not defined (infinite), because fewer than half of customers churned.
- By contract type: FILL IN from your plot (describe how fast month-to-month falls compared with one-year and two-year).
- Log-rank test across contract types: p < 1e-100 (the software printed 0.0, which is floating-point underflow, not a true zero).

## Cox proportional hazards model
- Concordance of the unstratified model: 0.85 (measured on the training data, so optimistic; it describes fit, not out-of-sample prediction).
- Proportional hazards test: assumption violated for Contract (one-year), MonthlyCharges, Partner and mailed-check payment (p < 0.005), borderline for fiber optic (p = 0.01). It holds for two-year contract, SeniorCitizen, PaperlessBilling, no-internet and credit-card payment.
- With about 7,000 rows the test detects small violations, so a failure means the effect is not exactly constant over time, not that the model is unusable.
- Stratified by Contract: concordance FILL IN. Assumption re-test (Cell 10): FILL IN which variables still fail.
- Stratified by Contract and monthly-charge band: concordance FILL IN. Concordance values from stratified and unstratified models are not on the same scale, so they are not compared directly.
- Key hazard ratios (exp(coef)) from the stratified model: FILL IN for payment method and internet service.

## Limitations
1. Hazard ratios describe associations, not causes.
2. Contract is each customer's current contract; some may have switched during their tenure.
3. Kaplan-Meier assumes censoring is unrelated to churn risk; this cannot be verified here.
4. Features overlap (for example MonthlyCharges and InternetService), so individual hazard ratios can change when features are added or removed.
5. Stratifying by Contract and charge band handles the assumption violations but removes hazard ratios for those variables.
6. Survival curves describe groups. They are not individual time-to-churn predictions.

## Customer lifetime value (revenue-based)
- All figures are REVENUE, not profit. The dataset has no costs or margins.
- Expected active months = area under the Kaplan-Meier survival curve (restricted mean survival time), estimated separately per contract type.
- Lifetime revenue (72-month window) = expected active months x average monthly charge.
- Forward 12-month revenue per customer = monthly charge x expected active months in the next 12, conditional on the customer having already survived to their current tenure.
- Limits: curves are not estimated beyond 72 months, so the forward window is shortened for customers above 60 months of tenure (their value is understated). The estimate uses contract type and tenure only, and is an association-based estimate, not a guarantee.