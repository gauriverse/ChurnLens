import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import (
    AnalysisRun, Customer, Dataset, ModelVersion, Prediction,
)

# external id, tenure, monthly charge, contract, probability, risk category
ROWS = [
    ("AAA-1", 2, 100.0, "Month-to-month", 0.80, "High"),    # exposure 960
    ("AAA-2", 5, 20.0, "Month-to-month", 0.60, "High"),     # exposure 144
    ("BBB-1", 30, 100.0, "One year", 0.30, "Medium"),       # exposure 360
    ("BBB-2", 40, 20.0, "One year", 0.10, "Low"),           # exposure 24
    ("CCC-1", 60, 90.0, "Two year", 0.02, "Low"),           # exposure 21.6
    ("CCC_2", 70, 60.0, "Two year", 0.02, "Low"),           # exposure 14.4, ties on probability
]
BY_PROBABILITY = ["AAA-1", "AAA-2", "BBB-1", "BBB-2", "CCC-1", "CCC_2"]


def make_engine_with_tables():
    # StaticPool: every connection sees the same in-memory database,
    # even though the API runs requests in other threads.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


def seed(engine):
    with Session(engine) as s:
        ds = Dataset(name="telco", row_count=len(ROWS), file_hash="h")
        mv = ModelVersion(name="churn", version="v1", algorithm="logreg", threshold=0.2)
        s.add_all([ds, mv])
        s.flush()
        run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed")
        later = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="running")
        s.add_all([run, later])
        s.flush()
        for ext, tenure, monthly, contract, prob, category in ROWS:
            c = Customer(
                dataset_id=ds.id, external_customer_id=ext, tenure=tenure,
                monthly_charges=monthly, contract=contract, features={},
            )
            s.add(c)
            s.flush()
            s.add(Prediction(
                analysis_run_id=run.id, customer_id=c.id, churn_probability=prob,
                risk_category=category, prediction_source="holdout_test",
            ))
        s.commit()
        return run.id, later.id


def client_for(engine):
    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


@pytest.fixture()
def seeded():
    engine = make_engine_with_tables()
    run_id, later_id = seed(engine)
    return client_for(engine), run_id, later_id


@pytest.fixture()
def empty_client():
    return client_for(make_engine_with_tables())


def ids(response):
    return [row["customer_id"] for row in response.json()["items"]]


def test_default_listing_is_ranked_by_probability_from_latest_completed_run(seeded):
    client, run_id, _ = seeded  # a newer, unfinished run exists and must be ignored
    response = client.get("/api/v1/customers")
    body = response.json()
    assert response.status_code == 200
    assert body["analysis_run_id"] == run_id
    assert body["total"] == 6
    assert ids(response) == BY_PROBABILITY
    first = body["items"][0]
    assert first["estimated_revenue_exposure"] == pytest.approx(960.0)
    assert first["monthly_charges"] == 100.0
    assert first["prediction_source"] == "holdout_test"
    assert body["exposure_horizon_months"] == 12


def test_sorting_by_exposure_differs_from_sorting_by_probability(seeded):
    client, _, _ = seeded
    response = client.get("/api/v1/customers", params={"sort_by": "estimated_revenue_exposure"})
    assert ids(response) == ["AAA-1", "BBB-1", "AAA-2", "BBB-2", "CCC-1", "CCC_2"]


def test_contract_filter_with_ascending_sort(seeded):
    client, _, _ = seeded
    response = client.get(
        "/api/v1/customers",
        params={"contract": "One year", "sort_by": "monthly_charges", "order": "asc"},
    )
    assert ids(response) == ["BBB-2", "BBB-1"]


def test_risk_filter_counts_match(seeded):
    client, _, _ = seeded
    response = client.get("/api/v1/customers", params={"risk": "High"})
    assert ids(response) == ["AAA-1", "AAA-2"]
    assert response.json()["total"] == 2


def test_search_is_case_insensitive_and_escapes_wildcards(seeded):
    client, _, _ = seeded
    assert ids(client.get("/api/v1/customers", params={"search": "bbb"})) == ["BBB-1", "BBB-2"]
    # an underscore must match only a literal underscore, not any character
    assert ids(client.get("/api/v1/customers", params={"search": "_"})) == ["CCC_2"]
    assert client.get("/api/v1/customers", params={"search": "%"}).json()["total"] == 0


def test_pages_do_not_overlap_and_cover_everything(seeded):
    client, _, _ = seeded
    page1 = client.get("/api/v1/customers", params={"page_size": 4, "page": 1})
    page2 = client.get("/api/v1/customers", params={"page_size": 4, "page": 2})
    page3 = client.get("/api/v1/customers", params={"page_size": 4, "page": 3})
    assert ids(page1) + ids(page2) == BY_PROBABILITY  # includes the tied CCC pair
    assert page2.json()["total"] == 6 and page2.json()["page"] == 2
    assert ids(page3) == [] and page3.json()["total"] == 6


@pytest.mark.parametrize("params", [
    {"risk": "Extreme"}, {"page": 0}, {"page_size": 101},
    {"sort_by": "password"}, {"order": "sideways"},
])
def test_invalid_query_parameters_return_422(seeded, params):
    client, _, _ = seeded
    assert client.get("/api/v1/customers", params=params).status_code == 422


def test_no_completed_run_returns_404(empty_client):
    assert empty_client.get("/api/v1/customers").status_code == 404


def test_unfinished_or_unknown_run_returns_404(seeded):
    client, _, later_id = seeded
    assert client.get("/api/v1/customers", params={"analysis_run_id": later_id}).status_code == 404
    assert client.get("/api/v1/customers", params={"analysis_run_id": 9999}).status_code == 404