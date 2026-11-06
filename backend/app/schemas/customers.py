from typing import Literal

from pydantic import BaseModel, Field

from backend.app.core.constants import EXPOSURE_HORIZON_MONTHS

RiskCategory = Literal["Low", "Medium", "High"]

EXPOSURE_NOTE = (
    "Exposure = churn probability x monthly charges x 12 months. It is an "
    "assumption-based measure of revenue exposed to churn, not a forecast of lost revenue."
)


class CustomerRow(BaseModel):
    customer_id: str
    churn_probability: float = Field(ge=0, le=1)
    risk_category: RiskCategory
    monthly_charges: float
    tenure: int
    contract: str | None
    estimated_revenue_exposure: float
    prediction_source: str


class CustomerPage(BaseModel):
    analysis_run_id: int
    total: int
    page: int
    page_size: int
    exposure_horizon_months: int = EXPOSURE_HORIZON_MONTHS
    exposure_note: str = EXPOSURE_NOTE
    items: list[CustomerRow]