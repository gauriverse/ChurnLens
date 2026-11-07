from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.segments import SegmentList
from backend.app.services.runs import resolve_run_id
from backend.app.services.segments import get_segments

router = APIRouter(prefix="/segments", tags=["segments"])


@router.get("", response_model=SegmentList)
def read_segments(
    analysis_run_id: int | None = Query(None, description="Defaults to the latest completed run"),
    db: Session = Depends(get_db),
):
    """Customer segments, highest retention priority first."""
    run_id = resolve_run_id(db, analysis_run_id)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no completed analysis run found")
    return get_segments(db, run_id)