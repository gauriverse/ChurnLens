from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database.base import Base
from backend.app.models.tables import (
    AnalysisRun, Customer, CustomerSegment, Dataset, ModelVersion, Prediction, Segment,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")  # SQLite ignores FKs by default

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def new_customer(dataset_id, external_id):
    return Customer(
        dataset_id=dataset_id, external_customer_id=external_id, tenure=1,
        monthly_charges=Decimal("29.85"), features={},
    )


def build(session, customer_ids=("C1",)):
    ds = Dataset(name="telco", row_count=len(customer_ids), file_hash="h1")
    mv = ModelVersion(name="churn", version="v1", algorithm="logreg", threshold=0.2)
    session.add_all([ds, mv])
    session.flush()
    run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id, status="completed")
    customers = [new_customer(ds.id, c) for c in customer_ids]
    session.add_all([run, *customers])
    session.flush()
    return ds, run, customers


def new_prediction(run, customer, probability=0.5, category="High"):
    return Prediction(
        analysis_run_id=run.id, customer_id=customer.id, churn_probability=probability,
        risk_category=category, prediction_source="holdout_test",
    )


def new_segment(run, cluster_id):
    return Segment(
        analysis_run_id=run.id, cluster_id=cluster_id, persona_name=f"Group {cluster_id}",
        size=10, churn_rate=0.2, avg_monthly_charges=Decimal("50"),
        revenue_at_risk_12m=Decimal("1000"), share_of_revenue_at_risk=0.5,
        retention_priority=cluster_id + 1, priority_tier="High",
    )


def test_duplicate_customer_id_in_same_dataset_is_rejected(session):
    ds, _, _ = build(session)
    session.add(new_customer(ds.id, "C1"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_same_customer_id_in_another_dataset_is_allowed(session):
    build(session)
    other = Dataset(name="bank", row_count=1, file_hash="h2")
    session.add(other)
    session.flush()
    session.add(new_customer(other.id, "C1"))
    session.flush()  # must not raise


def test_probability_outside_zero_one_is_rejected(session):
    _, run, (c,) = build(session)
    session.add(new_prediction(run, c, probability=1.5))
    with pytest.raises(IntegrityError):
        session.flush()


def test_invalid_risk_category_is_rejected(session):
    _, run, (c,) = build(session)
    session.add(new_prediction(run, c, category="Extreme"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_one_prediction_per_customer_per_run(session):
    _, run, (c,) = build(session)
    session.add(new_prediction(run, c))
    session.flush()
    session.add(new_prediction(run, c, probability=0.6))
    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_a_dataset_cascades_to_customers_and_predictions(session):
    ds, run, (c,) = build(session)
    session.add(new_prediction(run, c))
    session.flush()

    session.delete(ds)
    session.commit()

    assert session.scalar(select(func.count()).select_from(Customer)) == 0
    assert session.scalar(select(func.count()).select_from(Prediction)) == 0


def test_a_customer_has_one_segment_per_run(session):
    _, run, (c,) = build(session)
    s1, s2 = new_segment(run, 0), new_segment(run, 1)
    session.add_all([s1, s2])
    session.flush()

    session.add(CustomerSegment(analysis_run_id=run.id, customer_id=c.id, segment_id=s1.id))
    session.flush()
    session.add(CustomerSegment(analysis_run_id=run.id, customer_id=c.id, segment_id=s2.id))
    with pytest.raises(IntegrityError):
        session.flush()