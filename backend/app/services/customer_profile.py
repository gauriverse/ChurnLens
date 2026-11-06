from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, ModelVersion, Prediction,
    PredictionExplanation, RetentionRecommendation, Segment,
)
from churnlens.evaluation.risk import HIGH_RISK_CUTOFF
from churnlens.explainability.reasons import FEATURE_LABELS, strength

BAND_COUNT = 5     # probability bands of width 0.2, as in the calibration check
SMALL_BAND = 100   # fewer known outcomes than this and the observed rate is noisy
EXPOSURE_HORIZON_MONTHS = 12

SOURCE_NOTES = {
    "out_of_fold_train": (
        "This probability comes from a cross-validated model that did not see this "
        "customer when it was trained."
    ),
    "holdout_test": (
        "This customer was held out of training; the probability comes from a model "
        "that never saw them."
    ),
    "new_data": "This customer was scored after the model was trained.",
}


def probability_band(probability):
    """(low, high) edges of the 0.2-wide band containing the probability."""
    index = max(i for i in range(BAND_COUNT) if probability >= i / BAND_COUNT)
    return index / BAND_COUNT, (index + 1) / BAND_COUNT


def risk_category_definition(threshold):
    if threshold is None:
        return "Risk category cutoffs were not recorded for this model version."
    return (
        f"Low below {threshold:.2f}, Medium {threshold:.2f} to {HIGH_RISK_CUTOFF:.2f}, "
        f"High {HIGH_RISK_CUTOFF:.2f} and above (display cutoffs, not statistics)"
    )


def build_notes(*, prediction_source, tenure, probability, band_labeled, band_churned):
    """Context and data-quality notes, built only from real facts about this customer."""
    notes = []
    if prediction_source in SOURCE_NOTES:
        notes.append({"level": "info", "text": SOURCE_NOTES[prediction_source]})
    if tenure == 0:
        notes.append({
            "level": "warning",
            "text": (
                "This customer has 0 months of tenure and no billing history, so there is "
                "little behavioural information behind the prediction."
            ),
        })
    if band_labeled > 0:
        low, high = probability_band(probability)
        rate = band_churned / band_labeled
        notes.append({
            "level": "info",
            "text": (
                f"Among {band_labeled} customers in the same predicted-risk band "
                f"({low:.0%} to {high:.0%}) with known outcomes, {rate:.0%} actually churned."
            ),
        })
        if band_labeled < SMALL_BAND:
            notes.append({
                "level": "warning",
                "text": (
                    f"Only {band_labeled} customers with known outcomes fall in this "
                    "probability band, so the observed rate is noisy."
                ),
            })
    return notes


def get_customer_profile(db: Session, run_id: int, customer_id: str):
    """Everything about one customer in one analysis run, or None if not found."""
    run = db.get(AnalysisRun, run_id)
    row = db.execute(
        select(Customer, Prediction)
        .select_from(Customer)
        .join(
            Prediction,
            and_(Prediction.customer_id == Customer.id, Prediction.analysis_run_id == run_id),
        )
        .where(
            Customer.dataset_id == run.dataset_id,
            Customer.external_customer_id == customer_id,
        )
    ).first()
    if row is None:
        return None
    customer, prediction = row
    model = db.get(ModelVersion, run.model_version_id)

    explanations = db.scalars(
        select(PredictionExplanation)
        .where(PredictionExplanation.prediction_id == prediction.id)
        .order_by(PredictionExplanation.rank)
    ).all()
    segment = db.scalars(
        select(Segment)
        .join(CustomerSegment, CustomerSegment.segment_id == Segment.id)
        .where(
            CustomerSegment.analysis_run_id == run_id,
            CustomerSegment.customer_id == customer.id,
        )
    ).first()
    rec = db.scalars(
        select(RetentionRecommendation).where(
            RetentionRecommendation.analysis_run_id == run_id,
            RetentionRecommendation.customer_id == customer.id,
        )
    ).first()

    # Evidence from similar predictions: how many customers in the same band really churned
    probability = float(prediction.churn_probability)
    low, high = probability_band(probability)
    below_top = (
        Prediction.churn_probability <= high if high == 1.0
        else Prediction.churn_probability < high
    )
    labeled, churned = db.execute(
        select(
            func.count(Customer.churned),
            func.coalesce(func.sum(case((Customer.churned.is_(True), 1), else_=0)), 0),
        )
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .where(
            Prediction.analysis_run_id == run_id,
            Prediction.churn_probability >= low,
            below_top,
        )
    ).one()

    monthly = float(customer.monthly_charges)
    return {
        "analysis_run_id": run_id,
        "customer_id": customer.external_customer_id,
        "tenure": customer.tenure,
        "monthly_charges": monthly,
        "total_charges": None if customer.total_charges is None else float(customer.total_charges),
        "contract": customer.contract,
        "payment_method": customer.payment_method,
        "observed_churn": customer.churned,
        "model": {
            "name": model.name,
            "version": model.version,
            "algorithm": model.algorithm,
            "decision_threshold": model.threshold,
            "risk_category_definition": risk_category_definition(model.threshold),
        },
        "prediction": {
            "churn_probability": round(probability, 4),
            "risk_category": prediction.risk_category,
            "prediction_source": prediction.prediction_source,
            "estimated_revenue_exposure": round(
                probability * monthly * EXPOSURE_HORIZON_MONTHS, 2
            ),
        },
        "explanation": {
            "reason_text": prediction.reason_text,
            "top_reasons": [
                {
                    "rank": e.rank,
                    "feature": e.feature,
                    "label": FEATURE_LABELS.get(e.feature, e.feature),
                    "value": e.feature_value,
                    "contribution": round(e.shap_value, 4),
                    "direction": "raises" if e.shap_value >= 0 else "lowers",
                    "strength": strength(e.shap_value),
                }
                for e in explanations
            ],
        },
        "segment": None if segment is None else {
            "cluster_id": segment.cluster_id,
            "persona_name": segment.persona_name,
            "size": segment.size,
            "churn_rate": segment.churn_rate,
            "retention_priority": segment.retention_priority,
            "priority_tier": segment.priority_tier,
        },
        "recommendation": None if rec is None else {
            "priority_rank": rec.priority_rank,
            "expected_value": float(rec.expected_value),
            "reason_codes": [c for c in (rec.reason_codes or "").split("|") if c],
            "suggested_action": rec.suggested_action,
            "why_prioritized": rec.why_prioritized,
            "assumptions": rec.assumptions,
        },
        "notes": build_notes(
            prediction_source=prediction.prediction_source,
            tenure=customer.tenure,
            probability=probability,
            band_labeled=int(labeled),
            band_churned=int(churned),
        ),
    }