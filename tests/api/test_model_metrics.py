import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import AnalysisRun, Dataset, ModelVersion

METRICS = {
    "model_version": "v1",
    "algorithm": "logistic_regression + sigmoid calibration",
    "training_rows": 5634,
    "test_rows": 1409,
    "threshold": 0.2,
    "cost_assumptions": {"offer_cost": 40, "success_rate": 0.3, "horizon_months": 12, "margin": 1.0},
    "cv_train": {"roc_auc": 0.845, "brier": 0.135},
    "test": {
        "roc_auc": 0.842, "pr_auc": 0.633, "brier": 0.138, "mean_predicted": 0.268,
        "actual_churn_rate": 0.265, "precision": 0.467, "recall": 0.864, "f1": 0.606,
        "confusion_matrix": {"tn": 666, "fp": 369, "fn": 51, "tp": 323},
    },
    "test_campaign_at_threshold": {
        "threshold": 0.2, "targeted": 692, "churners_reached": 323, "campaign_cost": 27680,
        "estimated_retained": 96.89999999999999, "revenue_preserved": 86560.73999999999,
        "net_benefit": 58880.73999999999, "roi": 2.1271943641618494,
    },
    "test_campaign_contact_everyone": {
        "threshold": 0.0, "targeted": 1409, "churners_reached": 374, "campaign_cost": 56360,
        "estimated_retained": 112.2, "revenue_preserved": 97973.64,
        "net_benefit": 41613.64, "roi": 0.7383541518807665,
    },
}


def make_client(*, seeded=True, metrics=METRICS, with_dataset=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        with Session(engine) as s:
            ds = Dataset(name="Telco Customer Churn", source="kaggle", row_count=7043, file_hash="h")
            s.add(ds)
            s.flush()
            mv = ModelVersion(
                name="churn", version="v1", algorithm=METRICS["algorithm"],
                training_dataset_id=ds.id if with_dataset else None,
                metrics=metrics, threshold=0.2, is_active=True,
            )
            s.add(mv)
            s.flush()
            s.add(AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed"))
            s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_full_metrics_keep_cv_and_held_out_results_separate():
    response = make_client().get("/api/v1/model/metrics")
    assert response.status_code == 200
    body = response.json()

    assert body["model"]["name"] == "churn" and body["model"]["version"] == "v1"
    assert body["model"]["is_active"] is True
    assert body["training_dataset"] == {
        "name": "Telco Customer Churn", "source": "kaggle",
        "rows": 7043, "training_rows": 5634, "test_rows": 1409,
    }

    cv = body["cross_validation"]
    assert cv["roc_auc"] == 0.845 and cv["brier"] == 0.135
    assert "never saw them" in cv["note"]

    test = body["held_out_test"]
    assert test["customers"] == 1409 and test["churned"] == 374   # from the confusion matrix
    assert test["roc_auc"] == 0.842 and test["pr_auc"] == 0.633
    assert test["recall"] == 0.864 and test["precision"] == 0.467
    assert test["confusion_matrix"] == {"tn": 666, "fp": 369, "fn": 51, "tp": 323}
    assert "depend on the decision threshold" in test["note"]

    assert body["decision"]["threshold"] == 0.2
    assert body["decision"]["cost_assumptions"]["offer_cost"] == 40
    assert "not to maximise accuracy" in body["decision"]["note"]


def test_campaign_replay_is_labelled_hypothetical():
    campaign = make_client().get("/api/v1/model/metrics").json()["campaign_replay"]
    assert campaign["basis"].startswith("Hypothetical")
    at = campaign["at_threshold"]
    assert at["customers_targeted"] == 692 and at["churners_reached"] == 323
    assert at["net_benefit"] == pytest.approx(58880.74)
    assert at["roi"] == 2.13 and at["estimated_retained"] == 96.9
    everyone = campaign["contact_everyone"]
    assert everyone["customers_targeted"] == 1409
    assert everyone["net_benefit"] == pytest.approx(41613.64) and everyone["roi"] == 0.74


def test_notes_state_sample_size_and_that_performance_over_time_is_unverified():
    notes = make_client().get("/api/v1/model/metrics").json()["notes"]
    assert any("1409 customers (374 churned)" in n for n in notes)
    assert any("no new labeled data" in n for n in notes)


def test_missing_metrics_are_reported_as_missing_not_invented():
    body = make_client(metrics=None, with_dataset=False).get("/api/v1/model/metrics").json()
    assert body["training_dataset"] is None
    assert body["cross_validation"] is None
    assert body["held_out_test"] is None
    assert body["campaign_replay"] is None
    assert body["decision"]["threshold"] == 0.2
    assert len(body["notes"]) == 1 and "no new labeled data" in body["notes"][0]


def test_no_completed_run_returns_404():
    assert make_client(seeded=False).get("/api/v1/model/metrics").status_code == 404