import json

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from churnlens.explainability.export import top_contributions_long
from churnlens.explainability.reasons import explanation_text, top_reasons
from churnlens.explainability.shap_explainer import explain
from churnlens.features.preprocessing import FEATURES, TARGET
from churnlens.models.pipelines import build_pipeline

VERSION = "v1"

df = pd.read_csv("data/processed/telco_clean.csv")
train = pd.read_csv("data/processed/train.csv")
production = joblib.load(f"artifacts/churn_model_{VERSION}.joblib")

X_train, y_train = train[FEATURES], train[TARGET]
X_all = df[FEATURES]


pipe = build_pipeline("logistic_regression").fit(X_train, y_train)
grouped, baseline = explain(pipe, X_train, X_all)


reconstructed = baseline + grouped.sum(axis=1).to_numpy()
assert np.allclose(reconstructed, pipe.decision_function(X_all), atol=1e-6), "additivity failed"


prod_probs = production["model"].predict_proba(X_all)[:, 1]
rho = spearmanr(pipe.decision_function(X_all), prod_probs).correlation
print("rank agreement with production model:", round(rho, 4))
assert rho > 0.99, "explained model differs from production model"


long = top_contributions_long(grouped, X_all, df["customerID"].tolist(), n=5)
long.to_csv(f"data/processed/explanations_{VERSION}.csv", index=False)


texts = [
    explanation_text(top_reasons(grouped.iloc[i], X_all.iloc[i]))
    for i in range(len(df))
]
pd.DataFrame({"customerID": df["customerID"], "reason_text": texts}).to_csv(
    f"data/processed/customer_reasons_{VERSION}.csv", index=False
)


importance = grouped.abs().mean().sort_values(ascending=False).round(4)
with open(f"artifacts/global_importance_{VERSION}.json", "w") as f:
    json.dump(
        {"unit": "mean absolute SHAP value, log-odds scale",
         "baseline_log_odds": round(baseline, 4),
         "importance": importance.to_dict()},
        f, indent=2,
    )

print("customers explained:", len(df))
print("explanation rows:", len(long))
print(long.head(5).to_string(index=False))