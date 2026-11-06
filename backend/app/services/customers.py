from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from backend.app.core.constants import EXPOSURE_HORIZON_MONTHS
from backend.app.models.tables import Customer, Prediction


def list_customers(db: Session, run_id: int, *, search=None, contract=None, risk=None,
                   sort_by="churn_probability", order="desc", page=1, page_size=25):
    """One page of customers for an analysis run. Returns (total, list of dicts)."""
    # Cast to float so we get plain numbers back on every database
    monthly = cast(Customer.monthly_charges, Float)
    exposure = Prediction.churn_probability * monthly * EXPOSURE_HORIZON_MONTHS

    filters = [Prediction.analysis_run_id == run_id]
    if search:
        filters.append(Customer.external_customer_id.icontains(search, autoescape=True))
    if contract:
        filters.append(Customer.contract == contract)
    if risk:
        filters.append(Prediction.risk_category == risk)

    total = db.scalar(
        select(func.count())
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .where(*filters)
    )

    sort_expressions = {
        "churn_probability": Prediction.churn_probability,
        "estimated_revenue_exposure": exposure,
        "monthly_charges": monthly,
        "tenure": Customer.tenure,
    }
    expression = sort_expressions[sort_by]
    direction = expression.desc() if order == "desc" else expression.asc()

    rows = db.execute(
        select(
            Customer.external_customer_id.label("customer_id"),
            Prediction.churn_probability,
            Prediction.risk_category,
            monthly.label("monthly_charges"),
            Customer.tenure,
            Customer.contract,
            exposure.label("estimated_revenue_exposure"),
            Prediction.prediction_source,
        )
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .where(*filters)
        .order_by(direction, Prediction.id)  # Prediction.id makes the order deterministic
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).mappings().all()

    items = [
        {
            "customer_id": r["customer_id"],
            "churn_probability": round(r["churn_probability"], 4),
            "risk_category": r["risk_category"],
            "monthly_charges": round(r["monthly_charges"], 2),
            "tenure": r["tenure"],
            "contract": r["contract"],
            "estimated_revenue_exposure": round(r["estimated_revenue_exposure"], 2),
            "prediction_source": r["prediction_source"],
        }
        for r in rows
    ]
    return total, items