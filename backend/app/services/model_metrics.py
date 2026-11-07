from sqlalchemy.orm import Session

from backend.app.models.tables import AnalysisRun, Dataset, ModelVersion


def _campaign(d):
    roi = d.get("roi")
    return {
        "customers_targeted": int(d["targeted"]),
        "churners_reached": int(d["churners_reached"]),
        "campaign_cost": float(d["campaign_cost"]),
        "estimated_retained": round(float(d["estimated_retained"]), 1),
        "revenue_preserved": round(float(d["revenue_preserved"]), 2),
        "net_benefit": round(float(d["net_benefit"]), 2),
        "roi": None if roi is None or roi != roi else round(float(roi), 2),  # roi != roi is true only for NaN
    }


def _held_out(metrics):
    test = metrics.get("test")
    if not test:
        return None
    cm = test["confusion_matrix"]
    return {
        "customers": int(sum(cm.values())),   # sample sizes come from the confusion matrix
        "churned": int(cm["tp"] + cm["fn"]),
        "roc_auc": test["roc_auc"],
        "pr_auc": test["pr_auc"],
        "brier": test["brier"],
        "mean_predicted": test["mean_predicted"],
        "actual_churn_rate": test["actual_churn_rate"],
        "precision": test["precision"],
        "recall": test["recall"],
        "f1": test["f1"],
        "confusion_matrix": cm,
    }


def _campaign_section(metrics):
    at = metrics.get("test_campaign_at_threshold")
    everyone = metrics.get("test_campaign_contact_everyone")
    if not at or not everyone:
        return None
    return {"at_threshold": _campaign(at), "contact_everyone": _campaign(everyone)}


def build_model_notes(held_out):
    notes = []
    if held_out:
        notes.append(
            f"The held-out test set has {held_out['customers']} customers "
            f"({held_out['churned']} churned), so these metrics carry sampling uncertainty "
            "and small differences between models are not meaningful."
        )
    notes.append(
        "Performance over time has not been verified: no new labeled data has been "
        "evaluated since training."
    )
    return notes


def get_model_metrics(db: Session, run_id: int):
    run = db.get(AnalysisRun, run_id)
    model = db.get(ModelVersion, run.model_version_id)
    dataset = db.get(Dataset, model.training_dataset_id) if model.training_dataset_id else None
    m = model.metrics or {}
    held_out = _held_out(m)
    cv = m.get("cv_train")

    return {
        "analysis_run_id": run_id,
        "model": {
            "name": model.name,
            "version": model.version,
            "algorithm": model.algorithm,
            "is_active": model.is_active,
            "created_at": model.created_at,
        },
        "training_dataset": None if dataset is None else {
            "name": dataset.name,
            "source": dataset.source,
            "rows": dataset.row_count,
            "training_rows": m.get("training_rows"),
            "test_rows": m.get("test_rows"),
        },
        "cross_validation": None if not cv else {"roc_auc": cv["roc_auc"], "brier": cv["brier"]},
        "held_out_test": held_out,
        "decision": {"threshold": model.threshold, "cost_assumptions": m.get("cost_assumptions")},
        "campaign_replay": _campaign_section(m),
        "notes": build_model_notes(held_out),
    }