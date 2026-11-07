import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import AnalysisRun, Dataset, ModelVersion, Segment

FIBER = {
    "avg_tenure_months": 17.4, "avg_add_on_services": 1.62, "avg_contract_months": 1.3,
    "share_fiber": 1.0, "share_dsl": 0.0, "share_no_internet": 0.0,
    "share_of_churned_revenue_historical": 0.666,
}
DSL = {
    "avg_tenure_months": 16.4, "avg_add_on_services": 1.62, "avg_contract_months": 2.6,
    "share_fiber": 0.0, "share_dsl": 1.0, "share_no_internet": 0.0,
    "share_of_churned_revenue_historical": 0.137,
}

# inserted out of priority order on purpose
SEGMENTS = [
    dict(cluster_id=0, persona_name="Newer fiber, month-to-month", size=600, churn_rate=0.563,
         avg_monthly_charges=85.06, revenue_at_risk_12m=1119303.55,
         share_of_revenue_at_risk=0.665, retention_priority=1, priority_tier="High",
         characteristics=FIBER),
    dict(cluster_id=1, persona_name="No-internet customers", size=400, churn_rate=0.074,
         avg_monthly_charges=21.08, revenue_at_risk_12m=27498.47,
         share_of_revenue_at_risk=0.016, retention_priority=3, priority_tier="Low",
         characteristics=None),
    dict(cluster_id=2, persona_name="Newer DSL, short contracts", size=200, churn_rate=0.291,
         avg_monthly_charges=50.21, revenue_at_risk_12m=242986.12,
         share_of_revenue_at_risk=0.144, retention_priority=2, priority_tier="Medium",
         characteristics=DSL),
]


def make_client(*, seeded=True, with_segments=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        with Session(engine) as s:
            ds = Dataset(name="telco", row_count=1200, file_hash="h")
            mv = ModelVersion(name="churn", version="v1", algorithm="logreg")
            s.add_all([ds, mv])
            s.flush()
            run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed")
            s.add(run)
            s.flush()
            if with_segments:
                for seg in SEGMENTS:
                    s.add(Segment(analysis_run_id=run.id, **seg))
            s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


@pytest.fixture()
def client():
    return make_client()


def test_segments_are_ordered_by_priority_with_real_numbers(client):
    response = client.get("/api/v1/segments")
    body = response.json()
    assert response.status_code == 200
    assert body["total_customers"] == 1200
    assert [s["persona_name"] for s in body["segments"]] == [
        "Newer fiber, month-to-month", "Newer DSL, short contracts", "No-internet customers",
    ]
    assert [s["share_of_customers"] for s in body["segments"]] == [0.5, 0.1667, 0.3333]

    first = body["segments"][0]
    assert first["size"] == 600
    assert first["observed_churn_rate"] == 0.563
    assert first["revenue_at_risk_12m"] == pytest.approx(1119303.55)
    assert first["share_of_revenue_at_risk"] == 0.665
    assert first["priority_tier"] == "High"
    assert first["characteristics"]["share_fiber"] == 1.0
    assert first["description"] == (
        "Average tenure 17 months, $85.06 per month, 1.6 add-on services, "
        "contracts averaging 1.3 months. Internet: 100% fiber, 0% DSL, 0% none."
    )


def test_segment_without_characteristics_has_no_description(client):
    last = client.get("/api/v1/segments").json()["segments"][2]
    assert last["persona_name"] == "No-internet customers"
    assert last["characteristics"] is None
    assert last["description"] is None


def test_notes_state_the_method_and_the_cutoffs(client):
    body = client.get("/api/v1/segments").json()
    assert "Churn was not used" in body["method_note"]
    assert "30%" in body["priority_note"] and "10%" in body["priority_note"]
    assert "display cutoffs" in body["priority_note"]


def test_run_without_segments_returns_an_empty_list():
    body = make_client(with_segments=False).get("/api/v1/segments").json()
    assert body["segments"] == [] and body["total_customers"] == 0


def test_no_completed_run_returns_404():
    assert make_client(seeded=False).get("/api/v1/segments").status_code == 404