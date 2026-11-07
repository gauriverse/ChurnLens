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

URL = "/api/v1/simulate"

# external id, probability, monthly charge, segment cluster (None = in no segment)
CUSTOMERS = [
    ("C1", 0.80, 100.0, 0),
    ("C2", 0.60, 50.0, 0),
    ("C3", 0.30, 80.0, 1),
    ("C4", 0.10, 60.0, 1),
    ("C5", 0.05, 40.0, None),
    ("C6", 0.02, 20.0, 1),
]


def category(probability):
    if probability >= 0.5:
        return "High"
    return "Medium" if probability >= 0.2 else "Low"


def make_client(*, seeded=True, with_predictions=True):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        with Session(engine) as s:
            ds = Dataset(name="telco", row_count=len(CUSTOMERS), file_hash="h")
            mv = ModelVersion(name="churn", version="v1", algorithm="logreg", threshold=0.2)
            s.add_all([ds, mv])
            s.flush()
            run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed")
            s.add(run)
            s.flush()

            segments = {}
            for cluster_id, name in [(0, "Group A"), (1, "Group B")]:
                segment = Segment(
                    analysis_run_id=run.id, cluster_id=cluster_id, persona_name=name, size=3,
                    churn_rate=0.2, avg_monthly_charges=50.0, revenue_at_risk_12m=1000.0,
                    share_of_revenue_at_risk=0.5, retention_priority=cluster_id + 1,
                    priority_tier="High" if cluster_id == 0 else "Low",
                )
                s.add(segment)
                segments[cluster_id] = segment
            s.flush()

            for external_id, probability, charge, cluster in CUSTOMERS:
                customer = Customer(
                    dataset_id=ds.id, external_customer_id=external_id, tenure=12,
                    monthly_charges=charge, features={},
                )
                s.add(customer)
                s.flush()
                if with_predictions:
                    s.add(Prediction(
                        analysis_run_id=run.id, customer_id=customer.id,
                        churn_probability=probability, risk_category=category(probability),
                        prediction_source="holdout_test",
                    ))
                if cluster is not None:
                    s.add(CustomerSegment(
                        analysis_run_id=run.id, customer_id=customer.id,
                        segment_id=segments[cluster].id,
                    ))
            s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def scenario(name, **overrides):
    return {"name": name, "offer_cost": 10, "success_rate": 0.5, **overrides}


def post(client, *scenarios, **extra):
    return client.post(URL, json={"scenarios": list(scenarios), **extra})


def only(response):
    assert response.status_code == 200, response.text
    return response.json()["scenarios"][0]


def test_threshold_scenario_matches_hand_calculation():
    response = post(make_client(), scenario("S1", risk_threshold=0.1))
    s = only(response)
    body = response.json()

    assert body["customers_considered"] == 6
    assert body["basis"].startswith("Hypothetical")
    assert "different hypothetical worlds" in body["comparison_note"]
    assert s["assumptions"] == {
        "offer_cost": 10.0, "success_rate": 0.5, "risk_threshold": 0.1,
        "max_customers": None, "horizon_months": 12, "margin": 1.0,
    }
    assert s["customers_eligible"] == 4 and s["customers_targeted"] == 4
    assert s["campaign_cost"] == 40.0
    assert s["expected_retained_customers"] == pytest.approx(0.9)
    assert s["expected_revenue_preserved"] == pytest.approx(840.0)
    assert s["expected_net_benefit"] == pytest.approx(800.0)
    assert s["expected_roi"] == pytest.approx(20.0)
    assert s["value_basis"] == "revenue"
    assert s["warnings"] == []

    groups = s["by_segment"]
    assert [(g["persona_name"], g["customers_targeted"]) for g in groups] == [
        ("Group A", 2), ("Group B", 2),
    ]
    assert [g["campaign_cost"] for g in groups] == [20.0, 20.0]
    assert [g["expected_revenue_preserved"] for g in groups] == pytest.approx([660.0, 180.0])
    assert [g["expected_net_benefit"] for g in groups] == pytest.approx([640.0, 160.0])


def test_customer_cap_picks_best_expected_value_first():
    s = only(post(make_client(), scenario("S2", max_customers=2)))
    assert s["customers_eligible"] == 6 and s["customers_targeted"] == 2
    assert s["campaign_cost"] == 20.0
    assert s["expected_retained_customers"] == pytest.approx(0.7)
    assert s["expected_net_benefit"] == pytest.approx(640.0)   # customers C1 and C2
    assert s["expected_roi"] == pytest.approx(32.0)
    assert [g["persona_name"] for g in s["by_segment"]] == ["Group A"]
    assert s["warnings"] == []


def test_losing_customers_are_included_and_flagged():
    s = only(post(make_client(), scenario("S3")))   # no threshold, no cap: contact all six
    assert s["customers_targeted"] == 6 and s["campaign_cost"] == 60.0
    assert s["expected_retained_customers"] == pytest.approx(0.935, abs=0.006)
    assert s["expected_revenue_preserved"] == pytest.approx(854.4)
    assert s["expected_net_benefit"] == pytest.approx(794.4)
    assert s["expected_roi"] == pytest.approx(13.24)
    assert [g["persona_name"] for g in s["by_segment"]] == ["Group A", "Group B", "No segment"]
    assert [g["expected_net_benefit"] for g in s["by_segment"]] == pytest.approx([640.0, 152.4, 2.0])
    assert len(s["warnings"]) == 1
    assert "1 of 6" in s["warnings"][0] and "negative expected value" in s["warnings"][0]


def test_negative_net_benefit_is_reported_and_flagged():
    s = only(post(make_client(), scenario("S4", offer_cost=100, success_rate=0.1)))
    assert s["customers_targeted"] == 6 and s["campaign_cost"] == 600.0
    assert s["expected_revenue_preserved"] == pytest.approx(170.88)
    assert s["expected_net_benefit"] == pytest.approx(-429.12)
    assert s["expected_roi"] == -0.72
    assert any("6 of 6" in w for w in s["warnings"])
    assert any("Expected net benefit is negative" in w for w in s["warnings"])


def test_nobody_targeted_gives_zero_outcomes_and_no_roi():
    s = only(post(make_client(), scenario("S5", risk_threshold=0.99)))
    assert s["customers_eligible"] == 0 and s["customers_targeted"] == 0
    assert s["campaign_cost"] == 0.0 and s["expected_net_benefit"] == 0.0
    assert s["expected_roi"] is None
    assert s["by_segment"] == []
    assert len(s["warnings"]) == 1 and "No offers" in s["warnings"][0]


def test_cap_that_is_not_reached_is_flagged():
    s = only(post(make_client(), scenario("S6", risk_threshold=0.5, max_customers=5)))
    assert s["customers_eligible"] == 2 and s["customers_targeted"] == 2
    assert any("cap of 5" in w for w in s["warnings"])


def test_horizon_and_margin_change_the_value_and_are_labelled():
    s = only(post(make_client(), scenario("S7", risk_threshold=0.1, horizon_months=6, margin=0.5)))
    assert s["assumptions"]["horizon_months"] == 6 and s["assumptions"]["margin"] == 0.5
    assert s["value_basis"] == "revenue x 0.5 assumed margin"
    assert s["expected_revenue_preserved"] == pytest.approx(210.0)
    assert s["expected_net_benefit"] == pytest.approx(170.0)
    assert any("1 of 4" in w for w in s["warnings"])   # C4 is now worth -1


def test_several_scenarios_come_back_in_the_order_sent():
    response = post(
        make_client(), scenario("First", risk_threshold=0.1), scenario("Second", max_customers=2)
    )
    assert response.status_code == 200
    results = response.json()["scenarios"]
    assert [r["name"] for r in results] == ["First", "Second"]
    assert [r["customers_targeted"] for r in results] == [4, 2]


BAD_VALUES = [
    {"success_rate": 1.5}, {"offer_cost": 0}, {"offer_cost": -5}, {"risk_threshold": -0.1},
    {"risk_threshold": 1.1}, {"horizon_months": 0}, {"horizon_months": 61}, {"margin": 2},
    {"max_customers": -1}, {"name": ""},
]


@pytest.mark.parametrize("overrides", BAD_VALUES)
def test_out_of_range_values_return_422(overrides):
    assert post(make_client(), {**scenario("S"), **overrides}).status_code == 422


def test_missing_required_fields_return_422():
    response = make_client().post(URL, json={"scenarios": [{"name": "S", "success_rate": 0.5}]})
    assert response.status_code == 422


def test_scenario_list_must_have_one_to_five_unique_names():
    client = make_client()
    assert post(client).status_code == 422                       # none
    six = [scenario(f"S{i}") for i in range(6)]
    assert post(client, *six).status_code == 422                 # too many
    assert post(client, *six[:5]).status_code == 200             # exactly five is fine
    assert post(client, scenario("Same"), scenario("Same")).status_code == 422


def test_unknown_run_returns_404():
    assert post(make_client(), scenario("S"), analysis_run_id=9999).status_code == 404


def test_no_completed_run_returns_404():
    assert post(make_client(seeded=False), scenario("S")).status_code == 404


def test_run_without_predictions_returns_404():
    assert post(make_client(with_predictions=False), scenario("S")).status_code == 404


def test_browser_preflight_for_the_frontend_origin_is_allowed():
    response = make_client().options(URL, headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_internal_value_errors_become_422(monkeypatch):
    def refuse(*args, **kwargs):
        raise ValueError("bad input")

    monkeypatch.setattr("backend.app.services.simulate.select_targets", refuse)
    response = post(make_client(), scenario("S"))
    assert response.status_code == 422
    assert response.json() == {"detail": "bad input"}


def test_the_same_request_always_gives_the_same_answer():
    client = make_client()
    payload = [scenario("S", risk_threshold=0.1), scenario("T", max_customers=3)]
    assert post(client, *payload).json() == post(client, *payload).json()