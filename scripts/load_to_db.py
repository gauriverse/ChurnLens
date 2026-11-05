import hashlib
import json
import sys

import pandas as pd
from sqlalchemy import delete, func, insert, select

from backend.app.database.session import make_engine
from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, Dataset, ModelVersion, Prediction,
    PredictionExplanation, RetentionRecommendation, RetentionScenario, Segment,
)
from churnlens.evaluation.risk import risk_category

VERSION = "v1"
DATA = "data/processed"
REPLACE = "--replace" in sys.argv


def clean_value(v):
    """NaN -> None, so the database stores NULL."""
    return None if pd.isna(v) else v


def records(df):
    """DataFrame -> list of dicts with plain Python values (NaN becomes None)."""
    return json.loads(df.to_json(orient="records", double_precision=15))


def delete_existing(conn, dataset_id):
    """Remove a previous load. Deleting the dataset cascades to almost everything."""
    run_ids = select(AnalysisRun.id).where(AnalysisRun.dataset_id == dataset_id)
    conn.execute(delete(RetentionScenario).where(RetentionScenario.analysis_run_id.in_(run_ids)))
    conn.execute(delete(Dataset).where(Dataset.id == dataset_id))
    conn.execute(delete(ModelVersion).where(
        ModelVersion.name == "churn", ModelVersion.version == VERSION))


# ---- read the files produced by the earlier scripts ----
customers = pd.read_csv(f"{DATA}/telco_clean.csv")
preds = pd.read_csv(f"{DATA}/predictions_{VERSION}.csv")
reasons = pd.read_csv(f"{DATA}/customer_reasons_{VERSION}.csv")
explanations = pd.read_csv(f"{DATA}/explanations_{VERSION}.csv")
segments = pd.read_csv(f"{DATA}/segments_{VERSION}.csv")
cust_segments = pd.read_csv(f"{DATA}/customer_segments_{VERSION}.csv")
recs = pd.read_csv(f"{DATA}/retention_recommendations_{VERSION}.csv")
scenarios = pd.read_csv(f"{DATA}/scenario_comparison_{VERSION}.csv")
with open(f"artifacts/metrics_{VERSION}.json") as f:
    metrics = json.load(f)
with open(f"{DATA}/telco_clean.csv", "rb") as f:
    file_hash = hashlib.sha256(f.read()).hexdigest()

n = len(customers)
assert customers["customerID"].is_unique, "duplicate customer IDs"
assert len(preds) == n and len(reasons) == n and len(cust_segments) == n
assert len(explanations) == 5 * n, "expected 5 explanation rows per customer"

engine = make_engine()
with engine.begin() as conn:  # one transaction: all or nothing
    existing = conn.execute(select(Dataset.id).where(Dataset.file_hash == file_hash)).scalar()
    if existing is not None:
        if not REPLACE:
            raise SystemExit("This dataset is already loaded. Nothing changed. Use --replace to reload.")
        delete_existing(conn, existing)
        print("removed the previous load")

    dataset_id = conn.execute(insert(Dataset).values(
        name="Telco Customer Churn (Kaggle, blastchar)",
        source="kaggle",
        row_count=n,
        schema_json={c: str(t) for c, t in customers.dtypes.items()},
        file_hash=file_hash,
        is_reference=True,
    ).returning(Dataset.id)).scalar_one()

    model_id = conn.execute(insert(ModelVersion).values(
        name="churn", version=VERSION, algorithm=metrics["algorithm"],
        training_dataset_id=dataset_id, metrics=metrics, threshold=metrics["threshold"],
        artifact_path=f"artifacts/churn_model_{VERSION}.joblib", is_active=True,
    ).returning(ModelVersion.id)).scalar_one()

    run_id = conn.execute(insert(AnalysisRun).values(
        dataset_id=dataset_id, model_version_id=model_id, status="completed",
        finished_at=func.now(), summary={"customers": n},
    ).returning(AnalysisRun.id)).scalar_one()

    # customers (the full original row is kept as JSON in `features`)
    conn.execute(insert(Customer), [
        {"dataset_id": dataset_id, "external_customer_id": row["customerID"],
         "tenure": row["tenure"], "monthly_charges": row["MonthlyCharges"],
         "total_charges": row["TotalCharges"], "contract": row["Contract"],
         "payment_method": row["PaymentMethod"], "churned": bool(row["Churn"]),
         "features": row}
        for row in records(customers)
    ])
    id_of = dict(conn.execute(
        select(Customer.external_customer_id, Customer.id).where(Customer.dataset_id == dataset_id)
    ).all())

    # predictions (all out-of-sample) with risk category and reason text
    merged = preds.merge(reasons, on="customerID", how="left", validate="one_to_one")
    conn.execute(insert(Prediction), [
        {"analysis_run_id": run_id, "customer_id": id_of[r.customerID],
         "churn_probability": float(r.churn_probability),
         "risk_category": risk_category(float(r.churn_probability), metrics["threshold"]),
         "prediction_source": r.prediction_source,
         "reason_text": clean_value(r.reason_text)}
        for r in merged.itertuples(index=False)
    ])
    pred_of = dict(conn.execute(
        select(Prediction.customer_id, Prediction.id).where(Prediction.analysis_run_id == run_id)
    ).all())

    conn.execute(insert(PredictionExplanation), [
        {"prediction_id": pred_of[id_of[r.customerID]], "rank": int(r.rank),
         "feature": r.feature, "feature_value": clean_value(r.feature_value),
         "shap_value": float(r.shap_value)}
        for r in explanations.itertuples(index=False)
    ])

    # segments, then which customer is in which segment
    conn.execute(insert(Segment), [
        {"analysis_run_id": run_id, "cluster_id": int(r.cluster_id),
         "persona_name": r.persona_name, "size": int(r.size),
         "churn_rate": float(r.churn_rate), "avg_monthly_charges": float(r.avg_monthly),
         "revenue_at_risk_12m": float(r.revenue_at_risk_12m),
         "share_of_revenue_at_risk": float(r.share_of_revenue_at_risk),
         "retention_priority": int(r.retention_priority), "priority_tier": r.priority_tier}
        for r in segments.itertuples(index=False)
    ])
    segment_of = dict(conn.execute(
        select(Segment.cluster_id, Segment.id).where(Segment.analysis_run_id == run_id)
    ).all())
    conn.execute(insert(CustomerSegment), [
        {"analysis_run_id": run_id, "customer_id": id_of[r.customerID],
         "segment_id": segment_of[int(r.cluster_id)]}
        for r in cust_segments.itertuples(index=False)
    ])

    # recommendations (the assumptions are stored with every row)
    conn.execute(insert(RetentionRecommendation), [
        {"analysis_run_id": run_id, "customer_id": id_of[r.customerID],
         "priority_rank": int(r.priority_rank), "expected_value": float(r.expected_value),
         "reason_codes": clean_value(r.reason_codes),
         "suggested_action": clean_value(r.suggested_action),
         "why_prioritized": clean_value(r.why_prioritized),
         "assumptions": metrics["cost_assumptions"]}
        for r in recs.itertuples(index=False)
    ])

    # saved what-if scenarios: inputs in `params`, hypothetical outputs in `results`
    param_keys = ("offer_cost", "success_rate", "risk_threshold", "max_customers")
    conn.execute(insert(RetentionScenario), [
        {"name": rec["scenario"], "analysis_run_id": run_id,
         "params": {k: rec[k] for k in param_keys},
         "results": {k: v for k, v in rec.items() if k != "scenario" and k not in param_keys}}
        for rec in records(scenarios)
    ])

    # verify the row counts BEFORE the transaction commits
    def count(model, *conditions):
        return conn.execute(select(func.count()).select_from(model).where(*conditions)).scalar_one()

    pred_ids = select(Prediction.id).where(Prediction.analysis_run_id == run_id)
    checks = {
        "customers": (count(Customer, Customer.dataset_id == dataset_id), n),
        "predictions": (count(Prediction, Prediction.analysis_run_id == run_id), n),
        "explanations": (count(PredictionExplanation, PredictionExplanation.prediction_id.in_(pred_ids)), len(explanations)),
        "segments": (count(Segment, Segment.analysis_run_id == run_id), len(segments)),
        "customer_segments": (count(CustomerSegment, CustomerSegment.analysis_run_id == run_id), n),
        "recommendations": (count(RetentionRecommendation, RetentionRecommendation.analysis_run_id == run_id), len(recs)),
        "scenarios": (count(RetentionScenario, RetentionScenario.analysis_run_id == run_id), len(scenarios)),
    }
    for name, (got, want) in checks.items():
        print(f"{name:18} {got:>7}   (expected {want})")
        assert got == want, f"{name}: row count mismatch, rolling back"

print("loaded and committed. analysis_run id:", run_id)