import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import Customer, Dataset, ModelVersion
from backend.app.services.model_loader import clear_model_cache
from backend.app.services.predict import ADD_ON_SERVICES
from churnlens.evaluation.risk import risk_category
from churnlens.features.schema import CATEGORICAL_FEATURES, FEATURES
from churnlens.models.train import make_model

URL = "/api/v1/predict"
THRESHOLD = 0.2
ALGORITHM = "logistic_regression + sigmoid calibration"

ALLOWED = {name: ["No", "Yes"] for name in CATEGORICAL_FEATURES}
ALLOWED.update({name: ["No", "No internet service", "Yes"] for name in ADD_ON_SERVICES})
ALLOWED.update({
    "gender": ["Female", "Male"],
    "MultipleLines": ["No", "No phone service", "Yes"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaymentMethod": ["Electronic check", "Mailed check"],
})


def training_data(n=500):
    rng = np.random.default_rng(0)
    data = {
        "tenure": rng.integers(0, 73, n),
        "MonthlyCharges": rng.uniform(20, 100, n),
        "TotalCharges": rng.uniform(0, 5000, n),
        "SeniorCitizen": rng.integers(0, 2, n),
    }
    for name in CATEGORICAL_FEATURES:
        data[name] = rng.choice(ALLOWED[name], size=n)
    X = pd.DataFrame(data)[FEATURES]
    churn_chance = 1 / (1 + np.exp((X["tenure"] - 30) / 15))
    y = pd.Series((rng.uniform(size=n) < churn_chance).astype(int))
    return X, y


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    X, y = training_data()
    model = make_model().fit(X, y)
    path = tmp_path_factory.mktemp("model") / "model.joblib"
    joblib.dump(
        {"model": model, "threshold": THRESHOLD, "features": FEATURES, "version": "t1"}, path
    )
    return model, path


@pytest.fixture(autouse=True)
def fresh_model_cache():
    clear_model_cache()
    yield
    clear_model_cache()


def make_client(artifact_path, *, active=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        dataset = Dataset(name="Telco", row_count=2, file_hash="h")
        s.add(dataset)
        s.flush()
        for external_id, tenure, monthly, total in [("A", 0, 20.0, 0.0), ("B", 72, 100.0, 8000.0)]:
            s.add(Customer(
                dataset_id=dataset.id, external_customer_id=external_id, tenure=tenure,
                monthly_charges=monthly, total_charges=total, features={},
            ))
        s.add(ModelVersion(
            name="churn", version="v1", algorithm=ALGORITHM, training_dataset_id=dataset.id,
            artifact_path=str(artifact_path), threshold=THRESHOLD, is_active=active,
        ))
        s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def payload(**overrides):
    body = {
        "tenure": 12, "MonthlyCharges": 50.0, "TotalCharges": 600.0, "SeniorCitizen": 0,
        "gender": "Female", "Partner": "Yes", "Dependents": "No", "PhoneService": "Yes",
        "MultipleLines": "No", "InternetService": "DSL", "OnlineSecurity": "Yes",
        "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "Yes",
        "StreamingTV": "No", "StreamingMovies": "No", "Contract": "Month-to-month",
        "PaperlessBilling": "Yes", "PaymentMethod": "Mailed check",
    }
    body.update(overrides)
    return body


def warnings_of(body):
    return [n["text"] for n in body["notes"] if n["level"] == "warning"]


def test_prediction_matches_the_model_and_is_labelled(trained):
    model, path = trained
    sent = payload()
    response = make_client(path).post(URL, json=sent)
    assert response.status_code == 200, response.text
    body = response.json()

    expected = float(model.predict_proba(pd.DataFrame([sent], columns=FEATURES))[0, 1])
    assert body["churn_probability"] == pytest.approx(expected, abs=1e-4)
    assert body["risk_category"] == risk_category(expected, THRESHOLD)
    assert body["estimated_revenue_exposure"] == pytest.approx(expected * 50.0 * 12, abs=0.01)
    assert body["exposure_horizon_months"] == 12
    assert body["model"] == {
        "name": "churn", "version": "v1", "algorithm": ALGORITHM, "decision_threshold": 0.2,
        "risk_category_definition": (
            "Low below 0.20, Medium 0.20 to 0.50, High 0.50 and above "
            "(display cutoffs, not statistics)"
        ),
    }
    assert "not a certainty" in body["probability_note"]
    assert "assumption-based" in body["exposure_note"]


def test_clean_input_gets_only_the_info_note(trained):
    _, path = trained
    body = make_client(path).post(URL, json=payload()).json()
    assert warnings_of(body) == []
    assert body["notes"] == [
        {"level": "info", "text": "Scored from the values supplied. Nothing is stored."}
    ]


def test_data_quality_warnings_reach_the_response(trained):
    _, path = trained
    client = make_client(path)

    above_range = client.post(URL, json=payload(tenure=90)).json()
    assert any(
        w.startswith("tenure 90 is outside the range seen in the reference data (0 to 72)")
        for w in warnings_of(above_range)
    )

    conflict = client.post(URL, json=payload(InternetService="No")).json()
    assert any("inconsistent" in w for w in warnings_of(conflict))

    brand_new = client.post(URL, json=payload(tenure=0, TotalCharges=0.0)).json()
    assert any("0 months of tenure" in w for w in warnings_of(brand_new))


def test_unknown_category_is_rejected_with_the_allowed_values(trained):
    _, path = trained
    response = make_client(path).post(URL, json=payload(Contract="Weekly"))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0].startswith("Contract: 'Weekly' is not a value the model was trained on")
    assert "Month-to-month, One year, Two year" in detail[0]


@pytest.mark.parametrize("overrides", [
    {"tenure": -1}, {"tenure": 601}, {"MonthlyCharges": -5}, {"MonthlyCharges": "abc"},
    {"TotalCharges": -1}, {"SeniorCitizen": 2}, {"gender": "x" * 51}, {"Unexpected": 1},
])
def test_invalid_values_return_422(trained, overrides):
    _, path = trained
    assert make_client(path).post(URL, json=payload(**overrides)).status_code == 422


def test_missing_field_returns_422(trained):
    _, path = trained
    body = payload()
    del body["Contract"]
    assert make_client(path).post(URL, json=body).status_code == 422


def test_no_active_model_returns_503(trained):
    _, path = trained
    response = make_client(path, active=False).post(URL, json=payload())
    assert response.status_code == 503
    assert response.json() == {"detail": "no active model version with a stored model file"}


def test_missing_model_file_returns_503(tmp_path):
    response = make_client(tmp_path / "missing.joblib").post(URL, json=payload())
    assert response.status_code == 503
    assert response.json()["detail"].startswith("model file not found")


def test_model_expecting_other_features_returns_503(trained, tmp_path):
    model, _ = trained
    other = tmp_path / "other.joblib"
    joblib.dump(
        {"model": model, "threshold": THRESHOLD, "features": list(reversed(FEATURES)),
         "version": "bad"},
        other,
    )
    response = make_client(other).post(URL, json=payload())
    assert response.status_code == 503
    assert "different features" in response.json()["detail"]


def test_the_model_file_is_loaded_once_and_reused(trained, monkeypatch):
    _, path = trained
    calls = []
    real_load = joblib.load

    def counting_load(file):
        calls.append(file)
        return real_load(file)

    monkeypatch.setattr(joblib, "load", counting_load)
    client = make_client(path)
    for _ in range(3):
        assert client.post(URL, json=payload()).status_code == 200
    assert len(calls) == 1


def test_the_same_request_always_gives_the_same_answer(trained):
    _, path = trained
    client = make_client(path)
    assert client.post(URL, json=payload()).json() == client.post(URL, json=payload()).json()