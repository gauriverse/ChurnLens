import sys

import pandas as pd
from sqlalchemy import text

from backend.app.database.session import make_engine

if len(sys.argv) != 2:
    raise SystemExit("usage: python -m scripts.run_sql sql/<file>.sql")

with open(sys.argv[1], encoding="utf-8") as f:
    sql = f.read()

engine = make_engine()
with engine.connect() as conn:
    run = conn.execute(text(
        "select id, dataset_id from analysis_runs "
        "where status = 'completed' order by id desc limit 1"
    )).one()
    df = pd.read_sql(text(sql), conn, params={"run_id": run.id, "dataset_id": run.dataset_id})

print("analysis_run:", run.id, "| dataset:", run.dataset_id)
print(df.to_string(index=False))