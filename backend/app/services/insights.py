from sqlalchemy import Float, and_, case, cast, func, select
from sqlalchemy.orm import Session

from backend.app.core.constants import ALL_CUSTOMERS_GROUP, EXPOSURE_HORIZON_MONTHS
from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, Dataset, ModelVersion, Prediction, Segment,
)
from churnlens.evaluation.risk import HIGH_RISK_CUTOFF

# (upper edge in months, label); the last bucket is open-ended (49+ is 49-72 in the Telco data)
TENURE_BUCKETS = [(6, "0-6"), (12, "7-12"), (24, "13-24"), (48, "25-48"), (None, "49+")]

MONTHLY = cast(Customer.monthly_charges, Float)
EXPOSURE = Prediction.churn_probability * MONTHLY * EXPOSURE_HORIZON_MONTHS
# 1.0 if churned, 0.0 if not, NULL if unknown. AVG skips NULLs, so unknown outcomes are ignored.
CHURN_FLAG = case((Customer.churned.is_(True), 1.0), (Customer.churned.is_(False), 0.0))
TENURE_BUCKET_INDEX = case(
    *[(Customer.tenure <= upper, i)
      for i, (upper, _) in enumerate(TENURE_BUCKETS[:-1], start=1)],
    else_=len(TENURE_BUCKETS),
)

SURVIVAL_NOTE = (
    "Kaplan-Meier estimates from tenure and churn flags, treating customers who have not "
    "churned as still active (censored). The data are a single snapshot with no calendar dates, "
    "so these curves describe groups and are not individual time-to-churn predictions."
)
SURVIVAL_MISSING_NOTE = (
    "Survival curves have not been computed for this analysis run. "
    "Run scripts/store_survival.py to add them."
)


def survival_group(summary, group_key):
    """The stored survival numbers for one group, or None."""
    return (((summary or {}).get("survival") or {}).get("groups") or {}).get(group_key)


def build_survival_section(summary):
    """Curves exactly as stored. Nothing is computed here."""
    survival = (summary or {}).get("survival")
    if not survival or not survival.get("groups"):
        return {"available": False, "method": "Kaplan-Meier",
                "note": SURVIVAL_MISSING_NOTE, "curves": []}
    curves = [
        {
            "group": name,
            "customers": g["customers"],
            "events": g["events"],
            "horizon_months": g["horizon_months"],
            "expected_active_months": g["expected_active_months"],
            "survival_at": g["survival_at"],
            "points": g["points"],
        }
        for name, g in survival["groups"].items()
    ]
    return {"available": True, "method": survival.get("method", "Kaplan-Meier"),
            "note": SURVIVAL_NOTE, "curves": curves}


def _rate(numerator, denominator):
    return None if not denominator else round(numerator / denominator, 4)


def build_kpis(*, total, labeled, churned, avg_tenure, high, flagged,
               revenue_at_risk, threshold, survival):
    """The KPI list, each with a written definition and a basis."""
    churn_rate = _rate(churned, labeled)
    threshold_text = f"{threshold:.2f}" if threshold is not None else "the model's decision threshold"
    survival_at = (survival or {}).get("survival_at", {})
    horizon = (survival or {}).get("horizon_months")

    def kpi(key, label, value, unit, basis, definition):
        return {"key": key, "label": label, "value": value, "unit": unit,
                "basis": basis, "definition": definition}

    def survival_kpi(months):
        return kpi(
            f"survival_{months}m", f"Still active after {months} months",
            survival_at.get(str(months)), "share", "survival_estimate",
            f"Kaplan-Meier estimate of the probability that a customer is still active after "
            f"{months} months of tenure. Customers who have not churned are treated as still "
            f"active (censored).",
        )

    lifetime_window = (
        f"within the first {horizon} months of tenure" if horizon else "within the observed window"
    )
    return [
        kpi("total_customers", "Total customers", int(total), "customers", "observed",
            "Number of customers in the dataset (and contract filter, if one is applied)."),
        kpi("churn_rate", "Churn rate", churn_rate, "share", "observed",
            "Customers marked as churned divided by customers with a known outcome. "
            "Counted from the data, not predicted."),
        kpi("retention_rate", "Retention rate",
            None if churn_rate is None else round(1 - churn_rate, 4), "share", "observed",
            "1 minus the churn rate: the share of customers with a known outcome who did not churn."),
        kpi("high_risk_customers", "High-risk customers", int(high), "customers", "model_estimate",
            f"Customers whose predicted churn probability is {HIGH_RISK_CUTOFF:.2f} or higher. "
            "A calibrated estimate, not a certainty."),
        kpi("flagged_customers", "Customers above the decision threshold", int(flagged),
            "customers", "model_estimate",
            f"Customers whose predicted churn probability is at or above {threshold_text} "
            "(Medium and High risk). The threshold was chosen from assumed offer costs."),
        kpi("revenue_at_risk_12m", "Revenue at risk (12 months)", round(float(revenue_at_risk), 2),
            "currency", "model_estimate",
            f"Sum over customers of churn probability x monthly charges x {EXPOSURE_HORIZON_MONTHS} "
            f"months. A model-based exposure measure in revenue, not profit. The "
            f"{EXPOSURE_HORIZON_MONTHS}-month horizon is an assumption, and the figure is not a "
            "forecast of lost revenue."),
        kpi("avg_tenure_months", "Average tenure", round(float(avg_tenure), 1), "months", "observed",
            "Mean tenure of customers in months. It understates true lifetimes, because customers "
            "who have not churned are still active."),
        kpi("expected_active_months", "Average customer lifetime",
            (survival or {}).get("expected_active_months"), "months", "survival_estimate",
            f"Expected number of active months {lifetime_window}, from the Kaplan-Meier survival "
            "curve (the area under it). Unlike average tenure, it accounts for customers who "
            "are still active."),
        survival_kpi(12), survival_kpi(24), survival_kpi(48),
    ]


def _label(value):
    return "Unknown" if value is None else str(value)


def _breakdown(db, run, group_expr, sort_expr, filters, *, with_segments=False, label_of=_label):
    """Customers, observed churn rate, average prediction and revenue at risk per group."""
    query = (
        select(
            group_expr,
            func.count(),
            func.avg(CHURN_FLAG),
            func.avg(Prediction.churn_probability),
            func.coalesce(func.sum(EXPOSURE), 0.0),
        )
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
    )
    if with_segments:
        query = query.join(
            CustomerSegment,
            and_(CustomerSegment.customer_id == Customer.id,
                 CustomerSegment.analysis_run_id == run.id),
        ).join(Segment, Segment.id == CustomerSegment.segment_id)

    rows = db.execute(
        query.where(Prediction.analysis_run_id == run.id, *filters)
        .group_by(group_expr)
        .order_by(sort_expr)
    ).all()
    return [
        {
            "label": label_of(group),
            "customers": int(n),
            "observed_churn_rate": None if churn is None else round(float(churn), 4),
            "avg_predicted_probability": None if pred is None else round(float(pred), 4),
            "revenue_at_risk_12m": round(float(exposure), 2),
        }
        for group, n, churn, pred, exposure in rows
    ]


def get_insights(db: Session, run_id: int, contract=None):
    """KPIs, breakdowns and survival curves for one analysis run, or None if nothing matches."""
    run = db.get(AnalysisRun, run_id)
    dataset = db.get(Dataset, run.dataset_id)
    model = db.get(ModelVersion, run.model_version_id)

    filters = [Customer.dataset_id == run.dataset_id]
    if contract:
        filters.append(Customer.contract == contract)

    total, labeled, churned, avg_tenure = db.execute(
        select(
            func.count(),
            func.count(Customer.churned),  # counts only customers with a known outcome
            func.coalesce(func.sum(case((Customer.churned.is_(True), 1), else_=0)), 0),
            func.avg(Customer.tenure),
        ).select_from(Customer).where(*filters)
    ).one()
    if total == 0:
        return None

    high, flagged, revenue_at_risk = db.execute(
        select(
            func.coalesce(func.sum(case((Prediction.risk_category == "High", 1), else_=0)), 0),
            func.coalesce(
                func.sum(case((Prediction.risk_category.in_(["Medium", "High"]), 1), else_=0)), 0
            ),
            func.coalesce(func.sum(EXPOSURE), 0.0),
        )
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .where(Prediction.analysis_run_id == run_id, *filters)
    ).one()

    return {
        "analysis_run_id": run_id,
        "dataset_name": dataset.name,
        "model_version": f"{model.name} {model.version}",
        "filters": {"contract": contract} if contract else {},
        "kpis": build_kpis(
            total=total, labeled=labeled, churned=churned, avg_tenure=avg_tenure,
            high=high, flagged=flagged, revenue_at_risk=revenue_at_risk,
            threshold=model.threshold,
            survival=survival_group(run.summary, contract or ALL_CUSTOMERS_GROUP),
        ),
        "breakdowns": {
            "by_contract": _breakdown(db, run, Customer.contract, Customer.contract, filters),
            "by_tenure": _breakdown(
                db, run, TENURE_BUCKET_INDEX, TENURE_BUCKET_INDEX, filters,
                label_of=lambda i: TENURE_BUCKETS[int(i) - 1][1],
            ),
            "by_payment_method": _breakdown(
                db, run, Customer.payment_method, Customer.payment_method, filters
            ),
            "by_segment": _breakdown(
                db, run, Segment.persona_name, func.min(Segment.retention_priority),
                filters, with_segments=True,
            ),
        },
        "survival": build_survival_section(run.summary),
    }