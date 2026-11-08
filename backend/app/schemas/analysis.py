from datetime import datetime

from pydantic import BaseModel

HISTORY_NOTE = (
    "Runs are listed newest first, including unfinished ones. Counts are the rows stored "
    "for each run."
)


class RunDataset(BaseModel):
    id: int
    name: str
    rows: int
    is_reference: bool


class RunModel(BaseModel):
    name: str
    version: str
    algorithm: str


class RunItem(BaseModel):
    analysis_run_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    dataset: RunDataset
    model: RunModel
    predictions: int
    segments: int
    recommendations: int
    has_survival_curves: bool
    has_monitoring_results: bool


class RunHistory(BaseModel):
    total: int
    limit: int
    offset: int
    runs: list[RunItem]
    note: str = HISTORY_NOTE