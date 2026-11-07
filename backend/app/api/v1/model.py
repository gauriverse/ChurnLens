from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.model_metrics import ModelMetrics
from backend.app.services.model_metrics import get_model_metrics
from backend.app.services.runs import resolve_run_id

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/metrics", response_model=ModelMetrics)
def read_model_metrics(
    analysis_run_id: int | None = Query(None, description="Defaults to the latest completed run"),
    db: Session = Depends(get_db),
):
    """Evaluation metrics of the model behind an analysis run."""
    run_id = resolve_run_id(db, analysis_run_id)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no completed analysis run found")
    return get_model_metrics(db, run_id)