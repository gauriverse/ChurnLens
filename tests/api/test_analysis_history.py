import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import (
    AnalysisRun, Customer, Dataset, ModelVersion, Prediction, RetentionRecommendation, Segment,
)

URL = "/api/v1/analysis/history"


def make_client(*, seeded=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        with Session(engine) as s:
            reference = Dataset(name="Telco Customer Churn", row_count=2, file_hash="a",
                                is_reference=True)
            other = Dataset(name="Uploaded bank data", row_count=5, file_hash="b",
                            is_reference=False)
            mv = ModelVersion(name="churn", version="v1", algorithm="logreg")
            s.add_all([reference, other, mv])
            s.flush()

            first = AnalysisRun(
                dataset_id=reference.id, model_version_id=mv.id, status="completed",
                summary={"survival": {"groups": {"All customers": {}}},
                         "monitoring": {"computed_at": "x"}},
            )
            second = AnalysisRun(dataset_id=other.id, model_version_id=mv.id,
                                 status="running", summary=None)
            s.add_all([first, second])
            s.flush()

            customers = [
                Customer(dataset_id=reference.id, external_customer_id=f"C{i}", tenure=1,
                         monthly_charges=10.0, features={})
                for i in (1, 2)
            ]
            s.add_all(customers)
            s.flush()
            for customer in customers:
                s.add(Prediction(
                    analysis_run_id=first.id, customer_id=customer.id, churn_probability=0.5,
                    risk_category="High", prediction_source="holdout_test",
                ))
            s.add(Segment(
                analysis_run_id=first.id, cluster_id=0, persona_name="G", size=2, churn_rate=0.5,
                avg_monthly_charges=10.0, revenue_at_risk_12m=100.0, share_of_revenue_at_risk=1.0,
                retention_priority=1, priority_tier="High",
            ))
            s.add(RetentionRecommendation(
                analysis_run_id=first.id, customer_id=customers[0].id, priority_rank=1,
                expected_value=5.0,
            ))
            s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_runs_are_listed_newest_first_with_counts():
    response = make_client().get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2 and body["limit"] == 20 and body["offset"] == 0
    assert [r["analysis_run_id"] for r in body["runs"]] == [2, 1]

    unfinished, completed = body["runs"]
    assert unfinished["status"] == "running" and unfinished["finished_at"] is None
    assert unfinished["dataset"] == {
        "id": 2, "name": "Uploaded bank data", "rows": 5, "is_reference": False
    }
    assert (unfinished["predictions"], unfinished["segments"], unfinished["recommendations"]) == (0, 0, 0)
    assert unfinished["has_survival_curves"] is False
    assert unfinished["has_monitoring_results"] is False

    assert completed["status"] == "completed"
    assert completed["dataset"]["is_reference"] is True and completed["dataset"]["rows"] == 2
    assert completed["model"] == {"name": "churn", "version": "v1", "algorithm": "logreg"}
    assert (completed["predictions"], completed["segments"], completed["recommendations"]) == (2, 1, 1)
    assert completed["has_survival_curves"] is True
    assert completed["has_monitoring_results"] is True
    assert "newest first" in body["note"]


def test_pagination_returns_the_requested_slice():
    client = make_client()
    second = client.get(URL, params={"limit": 1, "offset": 1}).json()
    assert second["total"] == 2 and second["limit"] == 1 and second["offset"] == 1
    assert [r["analysis_run_id"] for r in second["runs"]] == [1]
    assert client.get(URL, params={"offset": 2}).json()["runs"] == []


def test_empty_database_gives_an_empty_list():
    body = make_client(seeded=False).get(URL).json()
    assert body["total"] == 0 and body["runs"] == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_paging_returns_422(params):
    assert make_client().get(URL, params=params).status_code == 422