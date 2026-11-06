from typing import Literal

from pydantic import BaseModel, Field

from backend.app.core.constants import EXPOSURE_HORIZON_MONTHS
from backend.app.schemas.customers import EXPOSURE_NOTE, RiskCategory

PROBABILITY_NOTE = (
    "A churn probability is a calibrated estimate of risk, not a certainty about this customer."
)
EXPLANATION_NOTE = (
    "Contributions are in log-odds units: positive values raise this customer's risk score, "
    "negative values lower it. Only the five largest contributions are stored. Tenure, monthly "
    "charges and total charges carry overlapping information, so their individual signs can look "
    "counterintuitive; the plain-English summary combines them. These describe what drives the "
    "model's score, not why a customer will leave."
)
RECOMMENDATION_BASIS = (
    "Hypothetical: based on an assumed offer cost and success rate, not on measured outcomes. "
    "A churn probability does not show that an offer works."
)


class ModelInfo(BaseModel):
    name: str
    version: str
    algorithm: str
    decision_threshold: float | None
    risk_category_definition: str


class PredictionInfo(BaseModel):
    churn_probability: float = Field(ge=0, le=1)
    risk_category: RiskCategory
    prediction_source: str
    estimated_revenue_exposure: float
    exposure_horizon_months: int = EXPOSURE_HORIZON_MONTHS
    exposure_note: str = EXPOSURE_NOTE


class Reason(BaseModel):
    rank: int
    feature: str
    label: str
    value: str | None
    contribution: float
    direction: Literal["raises", "lowers"]
    strength: str


class Explanation(BaseModel):
    unit: str = "log-odds"
    reason_text: str | None
    top_reasons: list[Reason]
    note: str = EXPLANATION_NOTE


class SegmentInfo(BaseModel):
    cluster_id: int
    persona_name: str
    size: int
    churn_rate: float
    retention_priority: int
    priority_tier: str


class RecommendationInfo(BaseModel):
    priority_rank: int
    expected_value: float
    reason_codes: list[str]
    suggested_action: str | None
    why_prioritized: str | None
    assumptions: dict | None
    basis: str = RECOMMENDATION_BASIS


class Note(BaseModel):
    level: Literal["info", "warning"]
    text: str


class CustomerProfile(BaseModel):
    analysis_run_id: int
    customer_id: str
    tenure: int
    monthly_charges: float
    total_charges: float | None
    contract: str | None
    payment_method: str | None
    observed_churn: bool | None  # the dataset's known historical outcome, if it has one
    model: ModelInfo
    prediction: PredictionInfo
    explanation: Explanation
    segment: SegmentInfo | None
    recommendation: RecommendationInfo | None  # None when an offer has no positive expected value
    probability_note: str = PROBABILITY_NOTE
    notes: list[Note]