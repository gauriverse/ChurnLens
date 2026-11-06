from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.tables import AnalysisRun


def resolve_run_id(db: Session, requested: int | None = None) -> int | None:
    """The requested run if it exists and is completed, else the latest completed run.

    Returns None when nothing matches.
    """
    query = select(AnalysisRun.id).where(AnalysisRun.status == "completed")
    if requested is not None:
        return db.scalar(query.where(AnalysisRun.id == requested))
    return db.scalar(query.order_by(AnalysisRun.id.desc()).limit(1))