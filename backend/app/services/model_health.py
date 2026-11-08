from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.models.tables import AnalysisRun, Customer, Dataset, ModelVersion, Prediction
from backend.app.schemas.model_health import (
    DATA_QUALITY_MISSING_NOTE, DATA_QUALITY_NOTE, DRIFT_MISSING_NOTE, DRIFT_NOTE, SIMULATED_NOTE,
)
from backend.app.services.insights import CHURN_FLAG
from churnlens.features.schema import check_schema

P = Prediction.churn_probability
BIN_COUNT = 10
# Thresholds in a CASE, not a cast to integer: PostgreSQL rounds on cast, SQLite truncates.
BIN_INDEX = case(
    *[(P < (i + 1) / BIN_COUNT, i) for i in range(BIN_COUNT - 1)], else_=BIN_COUNT - 1
)
RISK_ORDER = ["Low", "Medium", "High"]

SIM_TITLES = {
    "monthly_charges_up_20pct": "Monthly charges up 20%",
    "newer_customer_base": "Newer customer base",
}
PREDICTION_EFFECT_KEYS = (
    "mean_predicted_before", "mean_predicted_after",
    "share_flagged_before", "share_flagged_after",
)


# ---------- pure helpers (no database) ----------

def schema_explanation(report):
    if report["compatible"]:
        return (
            f"All {report['required_columns']} features the model requires are present "
            "with compatible types."
        )
    parts = []
    if report["missing_columns"]:
        parts.append("missing columns: " + ", ".join(report["missing_columns"]))
    if report["type_mismatches"]:
        parts.append(
            "columns with incompatible types: "
            + ", ".join(m["column"] for m in report["type_mismatches"])
        )
    return (
        "This model cannot score the dataset as it stands ("
        + "; ".join(parts)
        + "). Mapping the columns or retraining on this schema would be required."
    )


def build_schema_compatibility(schema_json):
    if not schema_json:
        return None
    report = check_schema(schema_json)
    return {**report, "explanation": schema_explanation(report)}


def feature_drift(name, result):
    return {
        "feature": name,
        "kind": result["kind"],
        "psi": result["psi"],
        "psi_label": result["psi_label"],
        "ks_statistic": result.get("ks_statistic"),
        "categories": result.get("categories"),
        "unseen_categories": result.get("unseen_categories"),
        "bin_upper_edges": result.get("bin_upper_edges"),
        "reference_share": result["reference_share"],
        "current_share": result["current_share"],
    }


def feature_rows(features):
    """Largest PSI first; ties by name, so the order is always the same."""
    ordered = sorted(features.items(), key=lambda item: (-item[1]["psi"], item[0]))
    return [feature_drift(name, result) for name, result in ordered]


def build_data_quality(monitoring):
    stored = (monitoring or {}).get("data_quality")
    if not stored:
        return {"available": False, "note": DATA_QUALITY_MISSING_NOTE}
    return {
        "available": True,
        "note": DATA_QUALITY_NOTE,
        "source": stored.get("source"),
        "rows": stored["rows"],
        "columns": stored["columns"],
        "complete_rows": stored["complete_rows"],
        "complete_rows_pct": stored["complete_rows_pct"],
        "columns_with_missing": stored.get("columns_with_missing", []),
        "handling": stored.get("handling", []),
        "after_cleaning": stored.get("after_cleaning"),
    }


def _report(stored, *, kind, key, title, description, reference, current, reference_rows,
            note, predictions_comparison, changed_columns=(), effect=None):
    return {
        "kind": kind,
        "key": key,
        "title": title,
        "description": description,
        "reference": reference,
        "current": current,
        "reference_rows": reference_rows,
        "current_rows": stored["current_rows"],
        "changed_columns": list(changed_columns),
        "note": note,
        "features": feature_rows(stored["features"]),
        "predictions": feature_drift("churn_probability", stored["predictions"]),
        "predictions_comparison": predictions_comparison,
        "prediction_effect": effect,
    }


def build_drift_section(monitoring):
    baseline = (monitoring or {}).get("baseline_drift")
    if not baseline:
        return {"available": False, "note": DRIFT_MISSING_NOTE,
                "computed_at": None, "measured": None, "simulated": []}

    training_rows = baseline.get("reference_rows")
    measured = _report(
        baseline, kind="measured", key="baseline",
        title="Measured: training vs held-out customers",
        description="Real held-out customers compared with the customers the model was trained on.",
        reference=baseline.get("reference", "training customers"),
        current=baseline.get("current", "held-out customers"),
        reference_rows=training_rows, note=baseline.get("note", ""),
        predictions_comparison=(
            "Predicted probabilities of the training customers (out-of-fold) compared "
            "with those of the held-out customers."
        ),
    )
    simulated = [
        _report(
            sim, kind="simulated", key=sim["key"],
            title=SIM_TITLES.get(sim["key"], sim["key"].replace("_", " ").capitalize()),
            description=sim["description"],
            reference="training customers",
            current="held-out customers after the alteration",
            reference_rows=training_rows, note=SIMULATED_NOTE,
            predictions_comparison=(
                "Predicted probabilities of the held-out customers before and after "
                "the alteration."
            ),
            changed_columns=sim["changed_columns"],
            effect={k: sim[k] for k in PREDICTION_EFFECT_KEYS},
        )
        for sim in monitoring.get("simulated_drift", [])
    ]
    return {"available": True, "note": DRIFT_NOTE, "computed_at": monitoring.get("computed_at"),
            "measured": measured, "simulated": simulated}


def build_performance(labeled_new_data):
    if labeled_new_data == 0:
        return {
            "status": "not_verified",
            "labeled_new_data_customers": 0,
            "explanation": (
                "Whether the model's performance has deteriorated cannot be verified yet. It "
                "needs customers scored after training whose outcomes are known, and none have "
                "been evaluated. The drift indicators above are not a substitute."
            ),
        }
    return {
        "status": "pending_evaluation",
        "labeled_new_data_customers": labeled_new_data,
        "explanation": (
            f"{labeled_new_data} customers scored after training have known outcomes, but no "
            "performance evaluation has been run on them yet, so no deterioration result is "
            "reported."
        ),
    }


# ---------- live database queries ----------

def load_database_completeness(db: Session, dataset_id: int):
    total, total_charges, contract, payment, churn = db.execute(
        select(
            func.count(),
            func.count(Customer.total_charges),   # counts only non-empty values
            func.count(Customer.contract),
            func.count(Customer.payment_method),
            func.count(Customer.churned),
        ).select_from(Customer).where(Customer.dataset_id == dataset_id)
    ).one()
    columns = []
    for name, present in [("total_charges", total_charges), ("contract", contract),
                          ("payment_method", payment), ("churned", churn)]:
        missing = total - present
        columns.append({
            "column": name,
            "missing": int(missing),
            "missing_pct": round(100 * missing / total, 2) if total else 0.0,
        })
    return {"customers": int(total), "columns": columns}


def load_prediction_distribution(db: Session, run_id: int):
    scope = (Prediction.analysis_run_id == run_id,)
    joined = Prediction.__table__.join(Customer.__table__, Customer.id == Prediction.customer_id)

    total, mean_predicted, observed = db.execute(
        select(func.count(), func.avg(P), func.avg(CHURN_FLAG))
        .select_from(joined).where(*scope)
    ).one()
    if not total:
        return {"total": 0, "mean_predicted": None, "observed_churn_rate": None,
                "bins": [], "by_risk_category": [], "by_source": []}

    rows = db.execute(
        select(BIN_INDEX, func.count(), func.avg(P), func.avg(CHURN_FLAG))
        .select_from(joined).where(*scope).group_by(BIN_INDEX)
    ).all()
    by_index = {int(i): (int(n), avg, churn) for i, n, avg, churn in rows}

    bins = []
    for i in range(BIN_COUNT):   # every bin is returned, empty ones included
        n, avg, churn = by_index.get(i, (0, None, None))
        bins.append({
            "from_probability": round(i / BIN_COUNT, 1),
            "to_probability": round((i + 1) / BIN_COUNT, 1),
            "customers": n,
            "share": round(n / total, 4),
            "avg_predicted": None if avg is None else round(float(avg), 4),
            "observed_churn_rate": None if churn is None else round(float(churn), 4),
        })

    risk = dict(db.execute(
        select(Prediction.risk_category, func.count()).where(*scope)
        .group_by(Prediction.risk_category)
    ).all())
    by_risk = [
        {"category": c, "customers": int(risk[c]), "share": round(risk[c] / total, 4)}
        for c in RISK_ORDER if c in risk
    ]

    sources = db.execute(
        select(Prediction.prediction_source, func.count(), func.avg(P)).where(*scope)
        .group_by(Prediction.prediction_source).order_by(Prediction.prediction_source)
    ).all()

    return {
        "total": int(total),
        "mean_predicted": round(float(mean_predicted), 4),
        "observed_churn_rate": None if observed is None else round(float(observed), 4),
        "bins": bins,
        "by_risk_category": by_risk,
        "by_source": [
            {"source": s, "customers": int(n), "mean_predicted": round(float(avg), 4)}
            for s, n, avg in sources
        ],
    }


def count_labeled_new_data(db: Session, run_id: int):
    return int(db.scalar(
        select(func.count())
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .where(
            Prediction.analysis_run_id == run_id,
            Prediction.prediction_source == "new_data",
            Customer.churned.is_not(None),
        )
    ))


def get_model_health(db: Session, run_id: int):
    run = db.get(AnalysisRun, run_id)
    dataset = db.get(Dataset, run.dataset_id)
    model = db.get(ModelVersion, run.model_version_id)
    monitoring = (run.summary or {}).get("monitoring")

    return {
        "analysis_run_id": run_id,
        "model": {"name": model.name, "version": model.version},
        "dataset": {"name": dataset.name, "rows": dataset.row_count},
        "schema_compatibility": build_schema_compatibility(dataset.schema_json),
        "data_quality": build_data_quality(monitoring),
        "database_completeness": load_database_completeness(db, run.dataset_id),
        "prediction_distribution": load_prediction_distribution(db, run_id),
        "drift": build_drift_section(monitoring),
        "performance": build_performance(count_labeled_new_data(db, run_id)),
    }