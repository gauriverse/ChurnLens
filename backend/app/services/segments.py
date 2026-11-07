from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.tables import Segment


def describe_segment(c, avg_monthly_charges):
    """Plain-English summary built only from the stored averages."""
    if not c:
        return None
    return (
        f"Average tenure {c['avg_tenure_months']:.0f} months, "
        f"${avg_monthly_charges:,.2f} per month, "
        f"{c['avg_add_on_services']:.1f} add-on services, "
        f"contracts averaging {c['avg_contract_months']:.1f} months. "
        f"Internet: {c['share_fiber']:.0%} fiber, {c['share_dsl']:.0%} DSL, "
        f"{c['share_no_internet']:.0%} none."
    )


def get_segments(db: Session, run_id: int):
    rows = db.scalars(
        select(Segment)
        .where(Segment.analysis_run_id == run_id)
        .order_by(Segment.retention_priority)
    ).all()
    total = sum(s.size for s in rows)
    return {
        "analysis_run_id": run_id,
        "total_customers": total,
        "segments": [
            {
                "cluster_id": s.cluster_id,
                "persona_name": s.persona_name,
                "description": describe_segment(s.characteristics, float(s.avg_monthly_charges)),
                "size": s.size,
                "share_of_customers": round(s.size / total, 4),
                "observed_churn_rate": round(s.churn_rate, 4),
                "avg_monthly_charges": round(float(s.avg_monthly_charges), 2),
                "revenue_at_risk_12m": round(float(s.revenue_at_risk_12m), 2),
                "share_of_revenue_at_risk": round(s.share_of_revenue_at_risk, 4),
                "retention_priority": s.retention_priority,
                "priority_tier": s.priority_tier,
                "characteristics": s.characteristics,
            }
            for s in rows
        ],
    }