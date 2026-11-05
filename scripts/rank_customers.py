import pandas as pd

from churnlens.simulator.priority import rank_customers, summarize_selection

VERSION = "v1"
# Assumptions, not measurements
ASSUMPTIONS = dict(offer_cost=40, success_rate=0.30, horizon_months=12, margin=1.0)

df = pd.read_csv("data/processed/telco_clean.csv")
preds = pd.read_csv(f"data/processed/predictions_{VERSION}.csv")
segs = pd.read_csv(f"data/processed/customer_segments_{VERSION}.csv")

data = (
    df[["customerID", "tenure", "MonthlyCharges", "Contract"]]
    .merge(preds[["customerID", "churn_probability"]], on="customerID")
    .merge(segs[["customerID", "persona_name"]], on="customerID")
)
assert len(data) == len(df), "merge changed the number of customers"

for label, budget in [("no budget limit", None), ("budget $20,000", 20000)]:
    ranked = rank_customers(data, budget=budget, **ASSUMPTIONS)
    summary = summarize_selection(ranked, **ASSUMPTIONS)
    print("=====", label, "=====")
    print({k: round(v, 2) for k, v in summary.items()})
    print(ranked[ranked["selected"]].groupby("persona_name").size().to_string())
    print()

print(ranked.head(10)[["customerID", "persona_name", "churn_probability",
                       "MonthlyCharges", "expected_value", "priority_rank"]].round(3).to_string(index=False))