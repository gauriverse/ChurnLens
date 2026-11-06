from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.customer_profile import CustomerProfile
from backend.app.schemas.customers import CustomerPage, RiskCategory
from backend.app.services.customer_profile import get_customer_profile
from backend.app.services.customers import list_customers
from backend.app.services.runs import resolve_run_id

router = APIRouter(prefix="/customers", tags=["customers"])

SortBy = Literal[
    "churn_probability", "estimated_revenue_exposure", "monthly_charges", "tenure"
]


@router.get("", response_model=CustomerPage)
def get_customers(
    search: str | None = Query(None, max_length=100, description="Part of a customer ID, case-insensitive"),
    contract: str | None = Query(None, max_length=50, description="Exact contract type"),
    risk: RiskCategory | None = Query(None, description="Risk category"),
    sort_by: SortBy = "churn_probability",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    analysis_run_id: int | None = Query(None, description="Defaults to the latest completed run"),
    db: Session = Depends(get_db),
):
    """Customers ranked by risk. Probabilities are calibrated estimates, not certainties."""
    run_id = resolve_run_id(db, analysis_run_id)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no completed analysis run found")

    total, items = list_customers(
        db, run_id, search=search, contract=contract, risk=risk,
        sort_by=sort_by, order=order, page=page, page_size=page_size,
    )
    return CustomerPage(
        analysis_run_id=run_id, total=total, page=page, page_size=page_size, items=items
    )


@router.get("/{customer_id}", response_model=CustomerProfile)
def get_customer(
    customer_id: str = Path(..., max_length=100, description="Customer ID as it appears in the dataset"),
    analysis_run_id: int | None = Query(None, description="Defaults to the latest completed run"),
    db: Session = Depends(get_db),
):
    """One customer: prediction, top model contributions, segment, recommendation and notes."""
    run_id = resolve_run_id(db, analysis_run_id)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no completed analysis run found")

    profile = get_customer_profile(db, run_id, customer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="customer not found in this analysis run")
    return profile