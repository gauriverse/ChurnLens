import pandas as pd

from churnlens.simulator.scenarios import compare_scenarios

VERSION = "v1"

df = pd.read_csv("data/processed/telco_clean.csv")
preds = pd.read_csv(f"data/processed/predictions_{VERSION}.csv")
data = df[["customerID", "MonthlyCharges"]].merge(
    preds[["customerID", "churn_probability"]], on="customerID"
)
assert len(data) == len(df), "merge changed the number of customers"

# Every setting here is an assumption chosen to explore, not a measurement
SCENARIOS = [
    dict(name="Baseline", offer_cost=40, success_rate=0.30, risk_threshold=0.20),
    dict(name="Stricter targeting", offer_cost=40, success_rate=0.30, risk_threshold=0.50),
    dict(name="Capped at 500 offers", offer_cost=40, success_rate=0.30,
         risk_threshold=0.20, max_customers=500),
    dict(name="Costly offer, better success", offer_cost=80, success_rate=0.45,
         risk_threshold=0.30),
    dict(name="Pessimistic success rate", offer_cost=40, success_rate=0.10,
         risk_threshold=0.20),
]

table = compare_scenarios(data, SCENARIOS)
table.to_csv(f"data/processed/scenario_comparison_{VERSION}.csv", index=False)

show = table[["scenario", "customers_targeted", "campaign_cost",
              "expected_retained_customers", "expected_revenue_preserved",
              "expected_net_benefit", "expected_roi"]]
print(show.round(2).to_string(index=False))
print("\nAll figures are hypothetical (assumed cost and success rate), in revenue not profit.")