from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.constants import EXPOSURE_HORIZON_MONTHS
from backend.app.schemas.customer_profile import PROBABILITY_NOTE, ModelInfo, Note
from backend.app.schemas.customers import EXPOSURE_NOTE, RiskCategory

ShortText = Annotated[str, Field(max_length=50)]


class CustomerFeatures(BaseModel):
    """One customer, using the same column names as the Telco dataset."""

    model_config = ConfigDict(extra="forbid")  # a misspelled field name is an error, not ignored

    tenure: int = Field(ge=0, le=600, description="Months as a customer")
    MonthlyCharges: float = Field(ge=0, le=10_000, allow_inf_nan=False)
    TotalCharges: float = Field(ge=0, le=1_000_000, allow_inf_nan=False)
    SeniorCitizen: Literal[0, 1]
    gender: ShortText
    Partner: ShortText
    Dependents: ShortText
    PhoneService: ShortText
    MultipleLines: ShortText
    InternetService: ShortText
    OnlineSecurity: ShortText
    OnlineBackup: ShortText
    DeviceProtection: ShortText
    TechSupport: ShortText
    StreamingTV: ShortText
    StreamingMovies: ShortText
    Contract: ShortText
    PaperlessBilling: ShortText
    PaymentMethod: ShortText


class PredictionResult(BaseModel):
    model: ModelInfo
    churn_probability: float = Field(ge=0, le=1)
    risk_category: RiskCategory
    estimated_revenue_exposure: float
    exposure_horizon_months: int = EXPOSURE_HORIZON_MONTHS
    exposure_note: str = EXPOSURE_NOTE
    probability_note: str = PROBABILITY_NOTE
    notes: list[Note]