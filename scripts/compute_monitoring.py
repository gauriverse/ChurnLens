import json
from datetime import datetime, timezone

import joblib
import pandas as pd
from sqlalchemy import select, update

from backend.app.database.session import make_engine
from backend.app.models.tables import AnalysisRun
from churnlens.data.quality import completeness_report, missing_mask
from churnlens.features.schema import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES
from churnlens.monitoring.drift import compare_features, compare_numeric

VERSION = "v1"
DATA = "data/processed"
RAW = "data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"

# ---- 1. data quality, measured on the raw file (before cleaning) ----
raw = pd.read_csv(RAW)
clean = pd.read_csv(f"{DATA}/telco_clean.csv")
quality = completeness_report(raw)

blank_total = missing_mask(raw)["TotalCharges"]
treated = int((blank_total & (raw["tenure"] == 0)).sum())
untreated = int((blank_total & (raw["tenure"] != 0)).sum())
assert untreated == 0, "TotalCharges is blank for customers who have been billed"

after = completeness_report(clean)
quality["source"] = "raw file, before cleaning"
quality["handling"] = (
    [{
        "column": "TotalCharges",
        "missing": treated,
        "treatment": "Set to 0: these customers have 0 months of tenure and have not been billed yet.",
    }]
    if treated else []
)
quality["after_cleaning"] = {
    "rows": after["rows"],
    "complete_rows": after["complete_rows"],
    "complete_rows_pct": after["complete_rows_pct"],
}

# ---- 2. measured baseline: training customers vs held-out test customers ----
train = pd.read_csv(f"{DATA}/train.csv")
test = pd.read_csv(f"{DATA}/test.csv")
preds = pd.read_csv(f"{DATA}/predictions_{VERSION}.csv")
p_train = preds.loc[preds["prediction_source"] == "out_of_fold_train", "churn_probability"].to_numpy()
p_test = preds.loc[preds["prediction_source"] == "holdout_test", "churn_probability"].to_numpy()
assert len(p_train) == len(train) and len(p_test) == len(test), "prediction counts differ from the splits"

baseline = {
    "kind": "measured",
    "reference": "training customers",
    "reference_rows": len(train),
    "current": "held-out test customers",
    "current_rows": len(test),
    "note": (
        "Both groups are random samples of the same dataset, so little shift is expected. "
        "This shows the noise floor, what 'no drift' looks like. It is not evidence about future data."
    ),
    "features": compare_features(train, test, NUMERIC_FEATURES, CATEGORICAL_FEATURES),
    "predictions": compare_numeric(p_train, p_test),
}

# ---- 3. simulated drift: perturb the test set and score it with the real model ----
production = joblib.load(f"artifacts/churn_model_{VERSION}.joblib")
model, threshold = production["model"], production["threshold"]
reference_scores = model.predict_proba(test[FEATURES])[:, 1]


def charges_up(df):
    out = df.copy()
    out["MonthlyCharges"] = out["MonthlyCharges"] * 1.2
    out["TotalCharges"] = out["TotalCharges"] * 1.2
    return out


def newer_customers(df):
    out = df.copy()
    out["tenure"] = (out["tenure"] * 0.5).astype(int)   # rounds down (values are never negative)
    out["TotalCharges"] = out["TotalCharges"] * 0.5
    return out


SIMULATIONS = [
    ("monthly_charges_up_20pct",
     "Every customer's monthly and total charges multiplied by 1.2",
     ("MonthlyCharges", "TotalCharges"), charges_up),
    ("newer_customer_base",
     "Every customer's tenure halved (rounded down) and total charges halved",
     ("tenure", "TotalCharges"), newer_customers),
]

simulated = []
for key, description, changed, make in SIMULATIONS:
    shifted = make(test)
    scores = model.predict_proba(shifted[FEATURES])[:, 1]
    features = compare_features(train, shifted, NUMERIC_FEATURES, CATEGORICAL_FEATURES)
    for column, result in features.items():
        if column not in changed:   # identical data must give identical results
            assert result == baseline["features"][column], f"{column} changed but was not perturbed"
    simulated.append({
        "kind": "simulated",
        "key": key,
        "description": description,
        "changed_columns": list(changed),
        "current_rows": len(shifted),
        "features": features,
        "predictions": compare_numeric(reference_scores, scores),
        "mean_predicted_before": round(float(reference_scores.mean()), 4),
        "mean_predicted_after": round(float(scores.mean()), 4),
        "share_flagged_before": round(float((reference_scores >= threshold).mean()), 4),
        "share_flagged_after": round(float((scores >= threshold).mean()), 4),
    })

monitoring = {
    "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "data_quality": quality,
    "baseline_drift": baseline,
    "simulated_drift": simulated,
}
json.dumps(monitoring, allow_nan=False)   # fails now if anything is NaN or not plain JSON

# ---- 4. store in the latest completed analysis run (existing summary keys are kept) ----
engine = make_engine()
with engine.begin() as conn:
    run = conn.execute(
        select(AnalysisRun.id, AnalysisRun.summary)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    ).one()
    summary = dict(run.summary or {})
    summary["monitoring"] = monitoring
    conn.execute(update(AnalysisRun).where(AnalysisRun.id == run.id).values(summary=summary))

# ---- 5. a short report ----
def top(features, n=4):
    ranked = sorted(features.items(), key=lambda item: item[1]["psi"], reverse=True)[:n]
    return [(name, f["psi"], f["psi_label"]) for name, f in ranked]


print("stored in analysis_run", run.id, "| summary keys now:", sorted(summary))
print(f"\nDATA QUALITY (raw file): {quality['complete_rows']} of {quality['rows']} rows complete "
      f"({quality['complete_rows_pct']}%)")
for item in quality["columns_with_missing"]:
    print("   missing:", item)
print("   after cleaning:", quality["after_cleaning"])

print("\nBASELINE (measured: training vs held-out test)")
print("   largest feature PSI:", top(baseline["features"]))
print("   KS statistics:", {k: v["ks_statistic"] for k, v in baseline["features"].items() if v["kind"] == "numeric"})
print("   prediction PSI:", baseline["predictions"]["psi"], baseline["predictions"]["psi_label"])

for sim in simulated:
    print(f"\nSIMULATED: {sim['key']} ({sim['description']})")
    print("   largest feature PSI:", top(sim["features"]))
    print("   prediction PSI:", sim["predictions"]["psi"], sim["predictions"]["psi_label"])
    print("   mean predicted:", sim["mean_predicted_before"], "->", sim["mean_predicted_after"],
          "| share above decision threshold:", sim["share_flagged_before"], "->", sim["share_flagged_after"])