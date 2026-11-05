# Retention prioritization and scenario findings (Telco dataset)

## Assumptions (hypothetical, not measured)

- Offer cost $40, offer success rate 30%, 12-month horizon. All figures are revenue, not profit.
- Probabilities are calibrated and out-of-sample (out-of-fold for training customers, held-out for test customers).
- A churn probability does not show that an offer works. Success rate and cost are inputs, not results.

## Ranking engine

- Expected value per customer = probability x success rate x monthly charge x 12 - offer cost.
- Customers with positive expected value are contacted, best first. Break-even is probability x monthly charge of about $11.11 under these assumptions.
- No budget: 3,541 customers contacted, cost $141,640, expected net benefit $322,655, ROI 2.28.
- Budget of $20,000 (500 offers): expected net benefit $100,400, ROI 5.02. 485 of the 500 are "Newer fiber, month-to-month" customers.

## Scenario comparison

| Scenario | Targeted | Cost | Expected net benefit | ROI |
| --- | --- | --- | --- | --- |
| Baseline (threshold 0.20) | 3,423 | $136,920 | $314,206 | 2.29 |
| Stricter targeting (threshold 0.50) | 1,551 | $62,040 | $229,738 | 3.70 |
| Capped at 500 offers | 500 | $20,000 | $100,400 | 5.02 |
| $80 offer, 45% success, threshold 0.30 | 2,692 | $215,360 | $398,263 | 1.85 |
| Pessimistic success rate (10%) | 3,423 | $136,920 | $13,455 | 0.10 |

## Findings

1. Ranking by expected value ($322,655) beats a probability cutoff at 0.20 ($314,206) under identical assumptions.
2. ROI and total net benefit rank the scenarios differently; the right choice depends on the business objective.
3. Results are very sensitive to the assumed success rate: at 10% the baseline net benefit falls from $314k to $13k.
4. The $80 / 45% scenario has the highest net benefit only because it assumes a higher success rate; scenarios with different assumptions are different worlds, not competing strategies.
5. Reason codes: month-to-month appears for 2,999 of 3,541 prioritized customers, so it barely separates them. The high-charges rule fires for only 89 customers because it requires model support, and the model's monthly-charges contribution overlaps with internet service type.

## Limitations

- One success rate is applied to every customer; real responses would differ by segment and offer.
- The ranking identifies who is likely to leave and is valuable, not who is persuadable.
- Revenue preserved ignores margin, discounting and customers who would have stayed anyway.
- Cutoffs for reason codes (12 months, 75th-percentile charge, 0.05 model support) are display choices, not statistics.
