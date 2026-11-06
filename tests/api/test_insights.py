import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, Dataset, ModelVersion, Prediction, Segment,
)

# id, tenure, monthly, contract, payment, churned (None = unknown), probability, category
CUSTOMERS = [
    ("C1", 2, 100.0, "Month-to-month", "Electronic check", True, 0.80, "High"),
    ("C2", 5, 50.0, "Month-to-month", "Electronic check", True, 0.60, "High"),
    ("C3", 10, 80.0, "Month-to-month", "Mailed check", False, 0.30, "Medium"),
    ("C4", 30, 60.0, "One year", "Mailed check", False, 0.10, "Low"),
    ("C5", 50, 40.0, "Two year", "Credit card", False, 0.05, "Low"),
    ("C6", 70, 20.0, "Two year", "Credit card", None, 0.02, "Low"),
]
SEGMENT_OF = {"C1": 0, "C2": 0, "C3": 0, "C4": 1, "C5": 1, "C6": 1}

SURVIVAL = {
    "method": "Kaplan-Meier",
    "groups": {
        "All customers": {
            "customers": 5, "events": 2, "horizon_months": 70, "expected_active_months": 55.5,
            "survival_at": {"12": 0.8, "24": 0.7, "48": 0.6},
            "points": [{"month": 0, "survival": 1.0}, {"month": 12, "survival": 0.8}],
        },
        "Month-to-month": {
            "customers": 3, "events": 2, "horizon_months": 70, "expected_active_months": 20.0,
            "survival_at": {"12": 0.5, "24": 0.4, "48": 0.3},
            "points": [{"month": 0, "survival": 1.0}, {"month": 12, "survival": 0.5}],
        },
    },
}


def seed(engine, summary):
    with Session(engine) as s:
        ds = Dataset(name="telco", row_count=len(CUSTOMERS), file_hash="h")
        mv = ModelVersion(name="churn", version="v1", algorithm="logreg", threshold=0.2)
        s.add_all([ds, mv])
        s.flush()
        run = AnalysisRun(
            dataset_id=ds.id, model_version_id=mv.id, status="completed", summary=summary
        )
        s.add(run)
        s.flush()

        segments = {}
        for cluster_id, name in [(0, "Group A"), (1, "Group B")]:
            seg = Segment(
                analysis_run_id=run.id, cluster_id=cluster_id, persona_name=name, size=3,
                churn_rate=0.2, avg_monthly_charges=50.0, revenue_at_risk_12m=1000.0,
                share_of_revenue_at_risk=0.5, retention_priority=cluster_id + 1,
                priority_tier="High" if cluster_id == 0 else "Low",
            )
            s.add(seg)
            segments[cluster_id] = seg
        s.flush()

        for ext, tenure, monthly, contract, payment, churned, prob, category in CUSTOMERS:
            c = Customer(
                dataset_id=ds.id, external_customer_id=ext, tenure=tenure,
                monthly_charges=monthly, contract=contract, payment_method=payment,
                churned=churned, features={},
            )
            s.add(c)
            s.flush()
            s.add(Prediction(
                analysis_run_id=run.id, customer_id=c.id, churn_probability=prob,
                risk_category=category, prediction_source="holdout_test",
            ))
            s.add(CustomerSegment(
                analysis_run_id=run.id, customer_id=c.id,
                segment_id=segments[SEGMENT_OF[ext]].id,
            ))
        s.commit()


def make_client(*, seeded=True, summary=None):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        seed(engine, summary)

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


@pytest.fixture()
def client():
    return make_client(summary={"survival": SURVIVAL})


def kpis(response):
    return {k["key"]: k for k in response.json()["kpis"]}


def breakdown(response, name):
    return response.json()["breakdowns"][name]


def test_kpis_match_hand_calculation(client):
    response = client.get("/api/v1/insights")
    assert response.status_code == 200
    k = kpis(response)

    assert k["total_customers"]["value"] == 6
    assert k["churn_rate"]["value"] == pytest.approx(0.4)       # 2 churned of the 5 with a known outcome
    assert k["retention_rate"]["value"] == pytest.approx(0.6)
    assert k["high_risk_customers"]["value"] == 2                # C1, C2
    assert k["flagged_customers"]["value"] == 3                  # C1, C2, C3
    assert "0.20" in k["flagged_customers"]["definition"]
    # 0.8*100*12 + 0.6*50*12 + 0.3*80*12 + 0.1*60*12 + 0.05*40*12 + 0.02*20*12
    assert k["revenue_at_risk_12m"]["value"] == pytest.approx(1708.8)
    assert k["avg_tenure_months"]["value"] == pytest.approx(27.8)  # 167 / 6
    assert k["expected_active_months"]["value"] == pytest.approx(55.5)
    assert k["survival_12m"]["value"] == pytest.approx(0.8)
    assert k["survival_24m"]["value"] == pytest.approx(0.7)
    assert k["survival_48m"]["value"] == pytest.approx(0.6)

    assert k["churn_rate"]["basis"] == "observed"
    assert k["revenue_at_risk_12m"]["basis"] == "model_estimate"
    assert k["survival_12m"]["basis"] == "survival_estimate"
    assert all(item["definition"] for item in k.values())


def test_breakdown_by_contract_and_tenure(client):
    response = client.get("/api/v1/insights")

    contracts = breakdown(response, "by_contract")
    assert [r["label"] for r in contracts] == ["Month-to-month", "One year", "Two year"]
    m2m, one, two = contracts
    assert m2m["customers"] == 3
    assert m2m["observed_churn_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert m2m["avg_predicted_probability"] == pytest.approx(1.7 / 3, abs=1e-4)
    assert m2m["revenue_at_risk_12m"] == pytest.approx(1608.0)
    assert one["observed_churn_rate"] == 0.0
    # C6's outcome is unknown, so only C5 counts toward the churn rate
    assert two["customers"] == 2 and two["observed_churn_rate"] == 0.0
    assert two["revenue_at_risk_12m"] == pytest.approx(28.8)

    tenure = breakdown(response, "by_tenure")
    assert [r["label"] for r in tenure] == ["0-6", "7-12", "25-48", "49+"]  # empty buckets are omitted
    assert [r["customers"] for r in tenure] == [2, 1, 1, 2]
    assert [r["observed_churn_rate"] for r in tenure] == [1.0, 0.0, 0.0, 0.0]


def test_breakdown_by_payment_method_and_segment(client):
    response = client.get("/api/v1/insights")

    payment = breakdown(response, "by_payment_method")
    assert [r["label"] for r in payment] == ["Credit card", "Electronic check", "Mailed check"]
    assert [r["revenue_at_risk_12m"] for r in payment] == pytest.approx([28.8, 1320.0, 360.0])

    segments = breakdown(response, "by_segment")
    assert [r["label"] for r in segments] == ["Group A", "Group B"]  # ordered by retention priority
    assert [r["customers"] for r in segments] == [3, 3]
    assert segments[0]["observed_churn_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert segments[1]["observed_churn_rate"] == 0.0
    assert [r["revenue_at_risk_12m"] for r in segments] == pytest.approx([1608.0, 100.8])


def test_every_breakdown_covers_every_customer(client):
    response = client.get("/api/v1/insights")
    for section in ["by_contract", "by_tenure", "by_payment_method", "by_segment"]:
        assert sum(r["customers"] for r in breakdown(response, section)) == 6


def test_contract_filter_narrows_everything_except_survival_curves(client):
    response = client.get("/api/v1/insights", params={"contract": "Month-to-month"})
    body = response.json()
    k = kpis(response)

    assert body["filters"] == {"contract": "Month-to-month"}
    assert k["total_customers"]["value"] == 3
    assert k["churn_rate"]["value"] == pytest.approx(2 / 3, abs=1e-4)
    assert k["revenue_at_risk_12m"]["value"] == pytest.approx(1608.0)
    assert k["avg_tenure_months"]["value"] == pytest.approx(5.7)
    # survival KPIs switch to that contract's stored curve
    assert k["survival_12m"]["value"] == pytest.approx(0.5)
    assert k["expected_active_months"]["value"] == pytest.approx(20.0)

    assert [r["label"] for r in breakdown(response, "by_contract")] == ["Month-to-month"]
    assert [r["label"] for r in breakdown(response, "by_tenure")] == ["0-6", "7-12"]
    assert [r["label"] for r in breakdown(response, "by_payment_method")] == ["Electronic check", "Mailed check"]
    assert [r["label"] for r in breakdown(response, "by_segment")] == ["Group A"]
    # all stored curves are still returned, so the dashboard can compare groups
    assert [c["group"] for c in body["survival"]["curves"]] == ["All customers", "Month-to-month"]


def test_missing_survival_is_reported_not_invented():
    client = make_client(summary={"customers": 6})  # the loader's summary, no survival key
    response = client.get("/api/v1/insights")
    body = response.json()
    k = kpis(response)

    assert body["survival"]["available"] is False
    assert body["survival"]["curves"] == []
    assert "store_survival" in body["survival"]["note"]
    for key in ["expected_active_months", "survival_12m", "survival_24m", "survival_48m"]:
        assert k[key]["value"] is None
    assert k["total_customers"]["value"] == 6   # the SQL-based KPIs are unaffected


def test_stored_survival_curves_are_passed_through(client):
    survival = client.get("/api/v1/insights").json()["survival"]
    assert survival["available"] is True
    assert survival["method"] == "Kaplan-Meier"
    assert "time-to-churn" in survival["note"]
    first = survival["curves"][0]
    assert first["group"] == "All customers"
    assert first["survival_at"] == {"12": 0.8, "24": 0.7, "48": 0.6}
    assert first["points"] == [{"month": 0, "survival": 1.0}, {"month": 12, "survival": 0.8}]


def test_unknown_contract_returns_404(client):
    assert client.get("/api/v1/insights", params={"contract": "Weekly"}).status_code == 404


def test_no_completed_run_returns_404():
    assert make_client(seeded=False).get("/api/v1/insights").status_code == 404


def test_overlong_contract_returns_422(client):
    assert client.get("/api/v1/insights", params={"contract": "x" * 51}).status_code == 422