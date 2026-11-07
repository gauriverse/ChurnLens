from pydantic import BaseModel, Field, model_validator

MAX_SCENARIOS = 5

BASIS_NOTE = (
    "Hypothetical. These figures are what-if calculations built on the assumptions you supply "
    "(offer cost, success rate, months of revenue kept). Churn probabilities are the model's "
    "out-of-sample estimates; a probability does not show that an offer works, and no offer "
    "outcomes have been measured. Figures are revenue, not profit, unless a margin below 1 is set."
)
COMPARISON_NOTE = (
    "Scenarios with different assumptions are different hypothetical worlds, not competing "
    "strategies. To compare fairly, change one assumption at a time."
)


class ScenarioInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    offer_cost: float = Field(
        gt=0, le=100_000, allow_inf_nan=False,
        description="Cost of one retention offer",
    )
    success_rate: float = Field(
        ge=0, le=1, allow_inf_nan=False,
        description="Assumed share of would-be churners that an offer retains",
    )
    risk_threshold: float = Field(
        0.0, ge=0, le=1, allow_inf_nan=False,
        description="Only customers with at least this churn probability are contacted",
    )
    max_customers: int | None = Field(
        None, ge=0, le=1_000_000,
        description="Optional cap on the number of offers; best expected value is contacted first",
    )
    horizon_months: int = Field(
        12, ge=1, le=60,
        description="Months of revenue a retained customer is assumed to keep paying",
    )
    margin: float = Field(
        1.0, ge=0, le=1, allow_inf_nan=False,
        description="Share of revenue counted as value. 1.0 = revenue; use less for an assumed margin",
    )


class SimulationRequest(BaseModel):
    analysis_run_id: int | None = None
    scenarios: list[ScenarioInput] = Field(min_length=1, max_length=MAX_SCENARIOS)

    @model_validator(mode="after")
    def names_must_be_unique(self):
        names = [s.name for s in self.scenarios]
        if len(set(names)) != len(names):
            raise ValueError("scenario names must be unique")
        return self


class Assumptions(BaseModel):
    offer_cost: float
    success_rate: float
    risk_threshold: float
    max_customers: int | None
    horizon_months: int
    margin: float


class SegmentOutcome(BaseModel):
    persona_name: str
    customers_targeted: int
    campaign_cost: float
    expected_revenue_preserved: float
    expected_net_benefit: float


class ScenarioResult(BaseModel):
    name: str
    assumptions: Assumptions
    customers_eligible: int      # meet the risk threshold, before any cap
    customers_targeted: int
    campaign_cost: float
    expected_retained_customers: float
    expected_revenue_preserved: float
    expected_net_benefit: float
    expected_roi: float | None   # None when nobody is contacted
    value_basis: str
    by_segment: list[SegmentOutcome]
    warnings: list[str]


class SimulationResponse(BaseModel):
    analysis_run_id: int
    customers_considered: int
    basis: str = BASIS_NOTE
    comparison_note: str = COMPARISON_NOTE
    scenarios: list[ScenarioResult]