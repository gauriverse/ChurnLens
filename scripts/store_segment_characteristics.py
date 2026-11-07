import pandas as pd
from sqlalchemy import select, update

from backend.app.database.session import make_engine
from backend.app.models.tables import AnalysisRun, Segment
from churnlens.segmentation.summary import characteristics

VERSION = "v1"
segments = pd.read_csv(f"data/processed/segments_{VERSION}.csv")

engine = make_engine()
with engine.begin() as conn:
    run_id = conn.execute(
        select(AnalysisRun.id)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    ).scalar_one()
    stored_sizes = dict(conn.execute(
        select(Segment.cluster_id, Segment.size).where(Segment.analysis_run_id == run_id)
    ).all())

    assert set(stored_sizes) == set(segments["cluster_id"].astype(int)), (
        "cluster ids differ between the file and the database"
    )
    for r in segments.itertuples(index=False):
        cluster = int(r.cluster_id)
        assert stored_sizes[cluster] == int(r.size), f"cluster {cluster}: size differs"
        conn.execute(
            update(Segment)
            .where(Segment.analysis_run_id == run_id, Segment.cluster_id == cluster)
            .values(characteristics=characteristics(r._asdict()))
        )
        print(cluster, characteristics(r._asdict()))

print("characteristics stored for analysis_run", run_id)