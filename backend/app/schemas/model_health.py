from typing import Literal

from pydantic import BaseModel

from churnlens.monitoring.drift import PSI_MAJOR, PSI_MODERATE

EVIDENCE_NOTE = (
    "Three kinds of evidence are kept apart on this page. Measured drift compares real samples "
    "of data. Simulated drift is a demonstration: data was deliberately altered to show how the "
    "indicators respond, and it does not describe anything that has happened. Performance "
    "deterioration can only be verified with new labeled data, and none has been evaluated."
)
PSI_NOTE = (
    "PSI (population stability index) compares a feature's distribution with the training data. "
    f"The cutoffs ({PSI_MODERATE:.2f} for moderate and {PSI_MAJOR:.2f} for major shift) are common "
    "rules of thumb, not statistical tests. KS is the largest gap between two cumulative "
    "distributions (0 means identical)."
)
DATA_QUALITY_NOTE = (
    "Measured on the raw file before cleaning, so missing values that cleaning repaired are "
    "still visible here."
)
DATA_QUALITY_MISSING_NOTE = (
    "Data quality results have not been computed for this analysis run. "
    "Run scripts/compute_monitoring.py to add them."
)
DATABASE_NOTE = "Counted live in the database, after cleaning."
DISTRIBUTION_NOTE = (
    "Computed live from the stored predictions, all of which are out-of-sample estimates. "
    "Observed churn rates use only customers with known outcomes, and bins with few customers "
    "are noisy."
)
DRIFT_NOTE = "Computed offline by scripts/compute_monitoring.py and stored with the analysis run."
DRIFT_MISSING_NOTE = (
    "Drift results have not been computed for this analysis run. "
    "Run scripts/compute_monitoring.py to add them."
)
SIMULATED_NOTE = (
    "Simulated: the held-out customers were deliberately altered to show how the drift "
    "indicators and predictions respond. Nothing here describes data that actually changed."
)


class ModelRef(BaseModel):
    name: str
    version: str


class DatasetRef(BaseModel):
    name: str
    rows: int


class TypeMismatch(BaseModel):
    column: str
    expected: str
    found: str


class SchemaCompatibility(BaseModel):
    compatible: bool
    required_columns: int
    missing_columns: list[str]
    type_mismatches: list[TypeMismatch]
    extra_columns: list[str]
    id_column_present: bool
    target_column_present: bool
    explanation: str
    source: str = "column types stored when the dataset was loaded"


class MissingColumn(BaseModel):
    column: str
    missing: int
    missing_pct: float


class Handling(BaseModel):
    column: str
    missing: int
    treatment: str


class AfterCleaning(BaseModel):
    rows: int
    complete_rows: int
    complete_rows_pct: float


class DataQuality(BaseModel):
    available: bool
    note: str
    source: str | None = None
    rows: int | None = None
    columns: int | None = None
    complete_rows: int | None = None
    complete_rows_pct: float | None = None
    columns_with_missing: list[MissingColumn] = []
    handling: list[Handling] = []
    after_cleaning: AfterCleaning | None = None


class DatabaseCompleteness(BaseModel):
    customers: int
    columns: list[MissingColumn]
    note: str = DATABASE_NOTE


class DistributionBin(BaseModel):
    from_probability: float
    to_probability: float
    customers: int
    share: float
    avg_predicted: float | None
    observed_churn_rate: float | None


class RiskCategoryCount(BaseModel):
    category: str
    customers: int
    share: float


class SourceSummary(BaseModel):
    source: str
    customers: int
    mean_predicted: float


class PredictionDistribution(BaseModel):
    total: int
    mean_predicted: float | None
    observed_churn_rate: float | None
    bins: list[DistributionBin]
    by_risk_category: list[RiskCategoryCount]
    by_source: list[SourceSummary]
    note: str = DISTRIBUTION_NOTE


class FeatureDrift(BaseModel):
    feature: str
    kind: Literal["numeric", "categorical"]
    psi: float
    psi_label: str
    ks_statistic: float | None
    categories: list[str] | None
    unseen_categories: list[str] | None
    bin_upper_edges: list[float] | None
    reference_share: list[float]
    current_share: list[float]


class PredictionEffect(BaseModel):
    mean_predicted_before: float
    mean_predicted_after: float
    share_flagged_before: float
    share_flagged_after: float


class DriftReport(BaseModel):
    kind: Literal["measured", "simulated"]
    key: str
    title: str
    description: str
    reference: str
    current: str
    reference_rows: int | None
    current_rows: int
    changed_columns: list[str]
    note: str
    features: list[FeatureDrift]
    predictions: FeatureDrift
    predictions_comparison: str
    prediction_effect: PredictionEffect | None


class DriftSection(BaseModel):
    available: bool
    note: str
    psi_note: str = PSI_NOTE
    computed_at: str | None = None
    measured: DriftReport | None = None
    simulated: list[DriftReport] = []


class PerformanceMonitoring(BaseModel):
    status: Literal["not_verified", "pending_evaluation"]
    labeled_new_data_customers: int
    explanation: str


class ModelHealth(BaseModel):
    analysis_run_id: int
    model: ModelRef
    dataset: DatasetRef
    schema_compatibility: SchemaCompatibility | None
    data_quality: DataQuality
    database_completeness: DatabaseCompleteness
    prediction_distribution: PredictionDistribution
    drift: DriftSection
    performance: PerformanceMonitoring
    evidence_note: str = EVIDENCE_NOTE