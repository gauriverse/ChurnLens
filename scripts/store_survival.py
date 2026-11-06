import pandas as pd
from sqlalchemy import select, update

from backend.app.core.constants import ALL_CUSTOMERS_GROUP
from backend.app.database.session import make_engine
from backend.app.models.tables import AnalysisRun, Customer
from churnlens.survival.curves import km_by_group

engine = make_engine()
with engine.begin() as conn:
    run = conn.execute(
        select(AnalysisRun.id, AnalysisRun.dataset_id, AnalysisRun.summary)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.id.desc())
        .limit(1)
    ).one()
    rows = conn.execute(
        select(Customer.tenure, Customer.churned, Customer.contract)
        .where(Customer.dataset_id == run.dataset_id)
    ).all()

    df = pd.DataFrame(rows, columns=["tenure", "churned", "contract"])
    groups = km_by_group(df, "contract", ALL_CUSTOMERS_GROUP)

    summary = dict(run.summary or {})  # keep what the loader stored
    summary["survival"] = {"method": "Kaplan-Meier", "groups": groups}
    conn.execute(
        update(AnalysisRun).where(AnalysisRun.id == run.id).values(summary=summary)
    )

print("stored for analysis_run", run.id)
for name, g in groups.items():
    print(
        f"{name:16} customers={g['customers']:>5} churned={g['events']:>5} "
        f"expected active months={g['expected_active_months']:>6} survival_at={g['survival_at']}"
    )