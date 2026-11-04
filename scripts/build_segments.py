import joblib
import pandas as pd

from churnlens.segmentation.features import build_segment_features
from churnlens.segmentation.personas import (
    add_revenue_at_risk, assign_names, fit_segmenter, profile_clusters,
)

VERSION = "v1"

df = pd.read_csv("data/processed/telco_clean.csv")
preds = pd.read_csv(f"data/processed/predictions_{VERSION}.csv")

# Probabilities in the same row order as df (every one is out-of-sample)
probs = (
    preds.set_index("customerID")
    .loc[df["customerID"], "churn_probability"]
    .to_numpy()
)

features = build_segment_features(df)
pipe, labels = fit_segmenter(features)

profile = profile_clusters(df, features, labels)
names = assign_names(profile)
profile = add_revenue_at_risk(profile, df, labels, probs)
profile["persona_name"] = names

# Safety checks
assert profile["customers"].sum() == len(df), "cluster sizes do not add up"
assert profile["customers"].min() >= 100, "a cluster is too small to act on"

# Outputs
segments = profile.reset_index().rename(columns={"cluster": "cluster_id"})
segments = segments.rename(columns={"customers": "size"}).round(3)
segments.to_csv(f"data/processed/segments_{VERSION}.csv", index=False)

pd.DataFrame({
    "customerID": df["customerID"],
    "cluster_id": labels,
    "persona_name": [names[c] for c in labels],
}).to_csv(f"data/processed/customer_segments_{VERSION}.csv", index=False)

joblib.dump(
    {"pipeline": pipe, "persona_names": names.to_dict(),
     "features": list(features.columns), "version": VERSION},
    f"artifacts/segmentation_{VERSION}.joblib",
)

show = segments.sort_values("retention_priority")[
    ["retention_priority", "persona_name", "size", "churn_rate", "avg_monthly",
     "share_of_churned_revenue", "share_of_revenue_at_risk", "priority_tier"]
]
print(show.to_string(index=False))