from collections import Counter

import pandas as pd

from churnlens.explainability.shap_explainer import explain
from churnlens.features.preprocessing import FEATURES, TARGET
from churnlens.models.pipelines import build_pipeline
from churnlens.simulator.priority import rank_customers
from churnlens.simulator.recommendations import (
    NO_DRIVER_TEXT, customer_reasons, why_prioritized,
)

VERSION = "v1"
# Assumptions, not measurements
ASSUMPTIONS = dict(offer_cost=40, success_rate=0.30, horizon_months=12, margin=1.0)

df = pd.read_csv("data/processed/telco_clean.csv")
train = pd.read_csv("data/processed/train.csv")
preds = pd.read_csv(f"data/processed/predictions_{VERSION}.csv")
segs = pd.read_csv(f"data/processed/customer_segments_{VERSION}.csv")

data = (
    df[["customerID", "tenure", "MonthlyCharges", "Contract"]]
    .merge(preds[["customerID", "churn_probability"]], on="customerID")
    .merge(segs[["customerID", "persona_name"]], on="customerID")
)
ranked = rank_customers(data, budget=None, **ASSUMPTIONS)
ranked = ranked[ranked["expected_value"] > 0]

# Same SHAP recipe as the explanations script, indexed by customerID
pipe = build_pipeline("logistic_regression").fit(train[FEATURES], train[TARGET])
grouped, _ = explain(pipe, train[FEATURES], df[FEATURES])
grouped.index = df["customerID"]

raw = df.set_index("customerID")
thresholds = {"high_charge": float(df["MonthlyCharges"].quantile(0.75))}
print("high-charge cutoff (75th percentile):", round(thresholds["high_charge"], 2))

rows, code_counts = [], Counter()
for _, r in ranked.iterrows():
    cid = r["customerID"]
    reasons = customer_reasons(raw.loc[cid], grouped.loc[cid], thresholds)
    code_counts.update(x["code"] for x in reasons)
    rows.append({
        "customerID": cid,
        "priority_rank": r["priority_rank"],
        "persona_name": r["persona_name"],
        "churn_probability": round(r["churn_probability"], 4),
        "MonthlyCharges": r["MonthlyCharges"],
        "expected_value": round(r["expected_value"], 2),
        "reason_codes": "|".join(x["code"] for x in reasons),
        "suggested_action": " ".join(x["action"] for x in reasons) or NO_DRIVER_TEXT,
        "why_prioritized": why_prioritized(
            r["priority_rank"], r["churn_probability"], r["MonthlyCharges"],
            r["expected_value"], ASSUMPTIONS["offer_cost"], ASSUMPTIONS["success_rate"],
        ),
    })

out = pd.DataFrame(rows)
out.to_csv(f"data/processed/retention_recommendations_{VERSION}.csv", index=False)

print("customers with a recommendation:", len(out))
print("with no rule-based driver:", int((out["reason_codes"] == "").sum()))
print("how often each reason code appears:", dict(code_counts))
for _, r in out.head(3).iterrows():
    print()
    print(r["customerID"], "|", r["reason_codes"])
    print(r["why_prioritized"])
    print(r["suggested_action"])