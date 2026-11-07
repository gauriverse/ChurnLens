from datetime import datetime

from pydantic import BaseModel

CV_NOTE = (
    "Computed on out-of-fold predictions for the training customers (5-fold cross-validation): "
    "each customer was scored by a model that never saw them."
)
HELD_OUT_NOTE = (
    "Computed once on customers held out of training and model selection. Precision, recall, F1 "
    "and the confusion matrix depend on the decision threshold; ROC-AUC, PR-AUC and the Brier "
    "score do not."
)
DECISION_NOTE = (
    "The threshold was chosen to maximise expected net benefit under an assumed offer cost and "
    "success rate, not to maximise accuracy. Different assumptions would give a different threshold."
)
CAMPAIGN_NOTE = (
    "Hypothetical: a replay of the decision rule on historical churn labels, using an assumed "
    "offer success rate. It does not show that offers work."
)


class ModelSummary(BaseModel):
    name: str
    version: str
    algorithm: str
    is_active: bool
    created_at: datetime


class DatasetSummary(BaseModel):
    name: str
    source: str | None
    rows: int
    training_rows: int | None
    test_rows: int | None


class CrossValidationMetrics(BaseModel):
    roc_auc: float
    brier: float
    note: str = CV_NOTE


class ConfusionMatrix(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int


class HeldOutMetrics(BaseModel):
    customers: int
    churned: int
    roc_auc: float
    pr_auc: float
    brier: float
    mean_predicted: float
    actual_churn_rate: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: ConfusionMatrix
    note: str = HELD_OUT_NOTE


class DecisionRule(BaseModel):
    threshold: float | None
    cost_assumptions: dict | None
    note: str = DECISION_NOTE


class CampaignReplay(BaseModel):
    customers_targeted: int
    churners_reached: int
    campaign_cost: float
    estimated_retained: float
    revenue_preserved: float
    net_benefit: float
    roi: float | None


class CampaignSection(BaseModel):
    at_threshold: CampaignReplay
    contact_everyone: CampaignReplay
    basis: str = CAMPAIGN_NOTE


class ModelMetrics(BaseModel):
    analysis_run_id: int
    model: ModelSummary
    training_dataset: DatasetSummary | None
    cross_validation: CrossValidationMetrics | None
    held_out_test: HeldOutMetrics | None
    decision: DecisionRule
    campaign_replay: CampaignSection | None
    notes: list[str]