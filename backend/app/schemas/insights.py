from typing import Literal

from pydantic import BaseModel

Unit = Literal["customers", "share", "currency", "months"]
Basis = Literal["observed", "model_estimate", "survival_estimate"]

BASIS_NOTE = (
    "Observed values are counted from the dataset. Model estimates use calibrated predicted "
    "probabilities, which are estimates and not certainties. Survival estimates come from a "
    "Kaplan-Meier analysis of tenure and churn flags. Revenue figures are revenue, not profit."
)


class Kpi(BaseModel):
    key: str
    label: str
    value: int | float | None
    unit: Unit
    basis: Basis
    definition: str


class GroupRow(BaseModel):
    label: str
    customers: int
    observed_churn_rate: float | None
    avg_predicted_probability: float | None
    revenue_at_risk_12m: float


class Breakdowns(BaseModel):
    by_contract: list[GroupRow]
    by_tenure: list[GroupRow]
    by_payment_method: list[GroupRow]
    by_segment: list[GroupRow]


class SurvivalPoint(BaseModel):
    month: int
    survival: float


class SurvivalCurve(BaseModel):
    group: str
    customers: int
    events: int
    horizon_months: int
    expected_active_months: float
    survival_at: dict[str, float]
    points: list[SurvivalPoint]


class SurvivalSection(BaseModel):
    available: bool
    method: str
    note: str
    curves: list[SurvivalCurve]


class Insights(BaseModel):
    analysis_run_id: int
    dataset_name: str
    model_version: str
    filters: dict[str, str]
    kpis: list[Kpi]
    breakdowns: Breakdowns
    survival: SurvivalSection
    basis_note: str = BASIS_NOTE