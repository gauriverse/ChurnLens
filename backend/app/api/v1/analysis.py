from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.analysis import RunHistory
from backend.app.services.analysis import list_runs

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/history", response_model=RunHistory)
def read_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Analysis runs, newest first."""
    return list_runs(db, limit, offset)