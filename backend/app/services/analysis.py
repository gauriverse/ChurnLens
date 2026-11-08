from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.tables import (
    AnalysisRun, Dataset, ModelVersion, Prediction, RetentionRecommendation, Segment,
)


def _counts(db: Session, model, run_ids):
    """Rows stored per analysis run, for one child table."""
    if not run_ids:
        return {}
    return dict(db.execute(
        select(model.analysis_run_id, func.count())
        .where(model.analysis_run_id.in_(run_ids))
        .group_by(model.analysis_run_id)
    ).all())


def _has_survival(summary):
    return bool(((summary or {}).get("survival") or {}).get("groups"))


def list_runs(db: Session, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(AnalysisRun))
    rows = db.execute(
        select(AnalysisRun, Dataset, ModelVersion)
        .select_from(AnalysisRun)
        .join(Dataset, Dataset.id == AnalysisRun.dataset_id)
        .join(ModelVersion, ModelVersion.id == AnalysisRun.model_version_id)
        .order_by(AnalysisRun.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    run_ids = [run.id for run, _, _ in rows]
    predictions = _counts(db, Prediction, run_ids)
    segments = _counts(db, Segment, run_ids)
    recommendations = _counts(db, RetentionRecommendation, run_ids)

    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "runs": [
            {
                "analysis_run_id": run.id,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "dataset": {
                    "id": dataset.id, "name": dataset.name,
                    "rows": dataset.row_count, "is_reference": dataset.is_reference,
                },
                "model": {
                    "name": model.name, "version": model.version, "algorithm": model.algorithm,
                },
                "predictions": int(predictions.get(run.id, 0)),
                "segments": int(segments.get(run.id, 0)),
                "recommendations": int(recommendations.get(run.id, 0)),
                "has_survival_curves": _has_survival(run.summary),
                "has_monitoring_results": bool((run.summary or {}).get("monitoring")),
            }
            for run, dataset, model in rows
        ],
    }