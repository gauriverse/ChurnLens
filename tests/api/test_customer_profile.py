import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, Dataset, ModelVersion, Prediction,
    PredictionExplanation, RetentionRecommendation, Segment,
)

# id, tenure, monthly, total, contract, payment, churned, probability, category, source
CUSTOMERS = [
    ("AAA-1", 2, 100.0, 200.0, "Month-to-month", "Electronic check", True, 0.80, "High", "holdout_test"),
    ("AAA-2", 5, 90.0, 450.0, "Month-to-month", "Mailed check", True, 0.90, "High", "out_of_fold_train"),
    ("AAA-3", 8, 80.0, 640.0, "Month-to-month", "Mailed check", False, 0.85, "High", "out_of_fold_train"),
    ("NEW-0", 0, 30.0, 0.0, "Month-to-month", "Mailed check", False, 0.10, "Low", "out_of_fold_train"),
]


def seed(engine):
    with Session(engine) as s:
        ds = Dataset(name="telco", row_count=4, file_hash="a")
        other = Dataset(name="other", row_count=1, file_hash="b")
        mv = ModelVersion(name="churn", version="v1", algorithm="logistic_regression + sigmoid calibration", threshold=0.2)
        s.add_all([ds, other, mv])
        s.flush()
        run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed")
        s.add(run)
        s.flush()

        db_ids, prediction_ids = {}, {}
        for ext, tenure, monthly, total, contract, payment, churned, prob, category, source in CUSTOMERS:
            c = Customer(
                dataset_id=ds.id, external_customer_id=ext, tenure=tenure, monthly_charges=monthly,
                total_charges=total, contract=contract, payment_method=payment,
                churned=churned, features={},
            )
            s.add(c)
            s.flush()
            p = Prediction(
                analysis_run_id=run.id, customer_id=c.id, churn_probability=prob,
                risk_category=category, prediction_source=source,
                reason_text="Factors raising this customer's churn risk score: tenure." if ext == "AAA-1" else None,
            )
            s.add(p)
            s.flush()
            db_ids[ext], prediction_ids[ext] = c.id, p.id

        s.add(Customer(dataset_id=other.id, external_customer_id="OTH-1", tenure=1,
                       monthly_charges=10.0, features={}))

        for rank, feature, value, shap in [
            (1, "tenure", "2 months", 1.2),
            (2, "Contract", "Month-to-month", 0.3),
            (3, "InternetService", "DSL", -0.4),
        ]:
            s.add(PredictionExplanation(
                prediction_id=prediction_ids["AAA-1"], rank=rank, feature=feature,
                feature_value=value, shap_value=shap,
            ))

        segments = []
        for cluster_id, name, tier in [(0, "Group A", "High"), (1, "Group B", "Low")]:
            seg = Segment(
                analysis_run_id=run.id, cluster_id=cluster_id, persona_name=name, size=10,
                churn_rate=0.2, avg_monthly_charges=50.0, revenue_at_risk_12m=1000.0,
                share_of_revenue_at_risk=0.5, retention_priority=cluster_id + 1, priority_tier=tier,
            )
            s.add(seg)
            segments.append(seg)
        s.flush()
        s.add(CustomerSegment(analysis_run_id=run.id, customer_id=db_ids["AAA-1"], segment_id=segments[0].id))
        s.add(CustomerSegment(analysis_run_id=run.id, customer_id=db_ids["NEW-0"], segment_id=segments[1].id))

        s.add(RetentionRecommendation(
            analysis_run_id=run.id, customer_id=db_ids["AAA-1"], priority_rank=1,
            expected_value=268.28, reason_codes="NEW_CUSTOMER|MONTH_TO_MONTH",
            suggested_action="Contact early.", why_prioritized="Rank 1: test.",
            assumptions={"offer_cost": 40, "success_rate": 0.3},
        ))
        s.commit()


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    seed(engine)

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_full_profile_for_a_high_risk_customer(client):
    response = client.get("/api/v1/customers/AAA-1")
    assert response.status_code == 200
    body = response.json()

    assert body["customer_id"] == "AAA-1"
    assert body["tenure"] == 2 and body["monthly_charges"] == 100.0 and body["total_charges"] == 200.0
    assert body["observed_churn"] is True
    assert body["model"]["decision_threshold"] == 0.2
    assert body["model"]["risk_category_definition"] == (
        "Low below 0.20, Medium 0.20 to 0.50, High 0.50 and above (display cutoffs, not statistics)"
    )

    pred = body["prediction"]
    assert pred["churn_probability"] == 0.8 and pred["risk_category"] == "High"
    assert pred["estimated_revenue_exposure"] == pytest.approx(960.0)
    assert pred["prediction_source"] == "holdout_test"

    reasons = body["explanation"]["top_reasons"]
    assert [r["rank"] for r in reasons] == [1, 2, 3]
    assert [r["feature"] for r in reasons] == ["tenure", "Contract", "InternetService"]
    assert [r["label"] for r in reasons][:2] == ["tenure", "contract type"]
    assert [r["direction"] for r in reasons] == ["raises", "raises", "lowers"]
    assert [r["strength"] for r in reasons] == ["strongly", "moderately", "moderately"]
    assert body["explanation"]["reason_text"].startswith("Factors raising")

    assert body["segment"]["persona_name"] == "Group A"
    rec = body["recommendation"]
    assert rec["reason_codes"] == ["NEW_CUSTOMER", "MONTH_TO_MONTH"]
    assert rec["assumptions"]["offer_cost"] == 40
    assert rec["basis"].startswith("Hypothetical")

    assert "not a certainty" in body["probability_note"]
    assert any(n["level"] == "info" and "67%" in n["text"] for n in body["notes"])
    assert any(n["level"] == "warning" and n["text"].startswith("Only 3") for n in body["notes"])


def test_brand_new_customer_has_a_warning_and_no_recommendation(client):
    body = client.get("/api/v1/customers/NEW-0").json()
    assert body["observed_churn"] is False
    assert body["recommendation"] is None
    assert body["explanation"]["top_reasons"] == []
    assert body["explanation"]["reason_text"] is None
    assert body["segment"]["persona_name"] == "Group B"
    assert any(n["level"] == "warning" and "0 months" in n["text"] for n in body["notes"])
    assert any("did not see this customer" in n["text"] for n in body["notes"])


@pytest.mark.parametrize("path", [
    "/api/v1/customers/NOPE",
    "/api/v1/customers/OTH-1",                      # exists, but in a different dataset
    "/api/v1/customers/AAA-1?analysis_run_id=9999",
])
def test_unknown_customer_or_run_returns_404(client, path):
    assert client.get(path).status_code == 404