import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api.deps import get_db
from backend.app.database.base import Base
from backend.app.main import create_app
from backend.app.models.tables import AnalysisRun, Customer, Dataset, ModelVersion, Prediction
from churnlens.features.schema import CATEGORICAL_FEATURES

URL = "/api/v1/model/health"

# external id, probability, risk category, source, churned (None = unknown), total charges
CUSTOMERS = [
    ("H1", 0.05, "Low", "out_of_fold_train", False, 10.0),
    ("H2", 0.15, "Low", "out_of_fold_train", False, 20.0),
    ("H3", 0.25, "Medium", "holdout_test", False, 30.0),
    ("H4", 0.55, "High", "out_of_fold_train", True, 40.0),
    ("H5", 0.95, "High", "holdout_test", True, 50.0),
    ("H6", 0.95, "High", "holdout_test", None, None),
]


def telco_schema():
    schema = {"tenure": "int64", "SeniorCitizen": "int64",
              "MonthlyCharges": "float64", "TotalCharges": "float64"}
    schema.update({name: "object" for name in CATEGORICAL_FEATURES})
    schema.update({"customerID": "object", "Churn": "int64"})
    return schema


def numeric(psi, ks, label="little or no shift"):
    return {"kind": "numeric", "psi": psi, "psi_label": label, "ks_statistic": ks,
            "bin_upper_edges": [10.0, 20.0],
            "reference_share": [0.3, 0.4, 0.3], "current_share": [0.31, 0.39, 0.3]}


def categorical(psi):
    return {"kind": "categorical", "psi": psi, "psi_label": "little or no shift",
            "categories": ["Month-to-month", "One year"], "unseen_categories": [],
            "reference_share": [0.6, 0.4], "current_share": [0.61, 0.39]}


MONITORING = {
    "computed_at": "2026-11-07T10:00:00+00:00",
    "data_quality": {
        "source": "raw file, before cleaning", "rows": 7043, "columns": 21,
        "complete_rows": 7032, "complete_rows_pct": 99.84,
        "columns_with_missing": [{"column": "TotalCharges", "missing": 11, "missing_pct": 0.16}],
        "handling": [{"column": "TotalCharges", "missing": 11,
                      "treatment": "Set to 0: these customers have not been billed yet."}],
        "after_cleaning": {"rows": 7043, "complete_rows": 7043, "complete_rows_pct": 100.0},
    },
    "baseline_drift": {
        "kind": "measured", "reference": "training customers", "reference_rows": 5634,
        "current": "held-out test customers", "current_rows": 1409,
        "note": "Both groups are random samples of the same dataset.",
        "features": {"tenure": numeric(0.004, 0.012), "Contract": categorical(0.002)},
        "predictions": numeric(0.003, 0.02),
    },
    "simulated_drift": [{
        "kind": "simulated", "key": "monthly_charges_up_20pct",
        "description": "Every customer's monthly and total charges multiplied by 1.2",
        "changed_columns": ["MonthlyCharges", "TotalCharges"], "current_rows": 1409,
        "features": {
            "tenure": numeric(0.004, 0.012), "Contract": categorical(0.002),
            "MonthlyCharges": numeric(0.31, 0.2, "major shift"),
            "TotalCharges": numeric(0.12, 0.1, "moderate shift"),
        },
        "predictions": numeric(0.05, 0.1),
        "mean_predicted_before": 0.268, "mean_predicted_after": 0.29,
        "share_flagged_before": 0.49, "share_flagged_after": 0.52,
    }],
}
FULL = {"monitoring": MONITORING}
SCHEMA = telco_schema()


def make_client(*, seeded=True, summary=FULL, schema=SCHEMA, labeled_new_data=False):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    if seeded:
        with Session(engine) as s:
            ds = Dataset(name="Telco Customer Churn", row_count=len(CUSTOMERS),
                         file_hash="h", schema_json=schema)
            mv = ModelVersion(name="churn", version="v1", algorithm="logreg", threshold=0.2)
            s.add_all([ds, mv])
            s.flush()
            run = AnalysisRun(dataset_id=ds.id, model_version_id=mv.id,
                              status="completed", summary=summary)
            s.add(run)
            s.flush()

            rows = list(CUSTOMERS)
            if labeled_new_data:
                rows.append(("N1", 0.5, "High", "new_data", True, 60.0))
            for ext, probability, category, source, churned, total_charges in rows:
                customer = Customer(
                    dataset_id=ds.id, external_customer_id=ext, tenure=12, monthly_charges=50.0,
                    total_charges=total_charges, contract="Month-to-month",
                    payment_method="Mailed check", churned=churned, features={},
                )
                s.add(customer)
                s.flush()
                s.add(Prediction(
                    analysis_run_id=run.id, customer_id=customer.id,
                    churn_probability=probability, risk_category=category,
                    prediction_source=source,
                ))
            s.commit()

    app = create_app()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def body_of(**kwargs):
    response = make_client(**kwargs).get(URL)
    assert response.status_code == 200, response.text
    return response.json()


def test_headline_fields_and_the_evidence_note():
    body = body_of()
    assert body["analysis_run_id"] == 1
    assert body["model"] == {"name": "churn", "version": "v1"}
    assert body["dataset"] == {"name": "Telco Customer Churn", "rows": 6}
    assert "Simulated drift is a demonstration" in body["evidence_note"]


def test_schema_compatibility_for_a_compatible_dataset():
    schema = body_of()["schema_compatibility"]
    assert schema["compatible"] is True
    assert schema["required_columns"] == 19
    assert schema["missing_columns"] == [] and schema["type_mismatches"] == []
    assert schema["id_column_present"] and schema["target_column_present"]
    assert "present with compatible types" in schema["explanation"]


def test_schema_incompatibility_is_explained():
    broken = telco_schema()
    del broken["Contract"]
    broken["TotalCharges"] = "object"
    schema = body_of(schema=broken)["schema_compatibility"]
    assert schema["compatible"] is False
    assert schema["missing_columns"] == ["Contract"]
    assert schema["type_mismatches"] == [
        {"column": "TotalCharges", "expected": "numeric", "found": "object"}
    ]
    assert "missing columns: Contract" in schema["explanation"]
    assert "incompatible types: TotalCharges" in schema["explanation"]
    assert "retraining" in schema["explanation"]


def test_missing_schema_is_reported_as_none():
    assert body_of(schema=None)["schema_compatibility"] is None


def test_data_quality_passes_through_stored_measurements():
    quality = body_of()["data_quality"]
    assert quality["available"] is True
    assert quality["source"] == "raw file, before cleaning"
    assert "before cleaning" in quality["note"]
    assert quality["rows"] == 7043 and quality["complete_rows"] == 7032
    assert quality["complete_rows_pct"] == 99.84
    assert quality["columns_with_missing"] == [
        {"column": "TotalCharges", "missing": 11, "missing_pct": 0.16}
    ]
    assert quality["handling"][0]["treatment"].startswith("Set to 0")
    assert quality["after_cleaning"] == {"rows": 7043, "complete_rows": 7043, "complete_rows_pct": 100.0}


def test_database_completeness_is_counted_live():
    completeness = body_of()["database_completeness"]
    assert completeness["customers"] == 6
    by_column = {c["column"]: c for c in completeness["columns"]}
    assert by_column["total_charges"] == {"column": "total_charges", "missing": 1, "missing_pct": 16.67}
    assert by_column["churned"]["missing"] == 1
    assert by_column["contract"]["missing"] == 0 and by_column["payment_method"]["missing"] == 0


def test_prediction_distribution_matches_hand_calculation():
    dist = body_of()["prediction_distribution"]
    assert dist["total"] == 6
    assert dist["mean_predicted"] == 0.4833          # (0.05+0.15+0.25+0.55+0.95+0.95) / 6
    assert dist["observed_churn_rate"] == 0.4        # 2 churned of the 5 with a known outcome

    bins = dist["bins"]
    assert len(bins) == 10
    assert (bins[3]["from_probability"], bins[3]["to_probability"]) == (0.3, 0.4)
    assert [b["customers"] for b in bins] == [1, 1, 1, 0, 0, 1, 0, 0, 0, 2]
    assert [b["share"] for b in bins] == [
        0.1667, 0.1667, 0.1667, 0.0, 0.0, 0.1667, 0.0, 0.0, 0.0, 0.3333
    ]
    assert [b["avg_predicted"] for b in bins] == [
        0.05, 0.15, 0.25, None, None, 0.55, None, None, None, 0.95
    ]
    # the last bin holds H5 (churned) and H6 (unknown outcome): only H5 counts
    assert [b["observed_churn_rate"] for b in bins] == [
        0.0, 0.0, 0.0, None, None, 1.0, None, None, None, 1.0
    ]

    assert [(c["category"], c["customers"]) for c in dist["by_risk_category"]] == [
        ("Low", 2), ("Medium", 1), ("High", 3),
    ]
    assert [c["share"] for c in dist["by_risk_category"]] == [0.3333, 0.1667, 0.5]
    assert dist["by_source"] == [
        {"source": "holdout_test", "customers": 3, "mean_predicted": 0.7167},
        {"source": "out_of_fold_train", "customers": 3, "mean_predicted": 0.25},
    ]
    assert "out-of-sample" in dist["note"]


def test_measured_and_simulated_drift_are_kept_apart():
    drift = body_of()["drift"]
    assert drift["available"] is True
    assert drift["computed_at"] == "2026-11-07T10:00:00+00:00"
    assert "rules of thumb" in drift["psi_note"]

    measured = drift["measured"]
    assert measured["kind"] == "measured" and measured["key"] == "baseline"
    assert measured["reference_rows"] == 5634 and measured["current_rows"] == 1409
    assert measured["changed_columns"] == [] and measured["prediction_effect"] is None
    assert [f["feature"] for f in measured["features"]] == ["tenure", "Contract"]
    assert measured["features"][0]["ks_statistic"] == 0.012
    assert measured["features"][1]["ks_statistic"] is None
    assert measured["features"][1]["categories"] == ["Month-to-month", "One year"]
    assert measured["predictions"]["feature"] == "churn_probability"

    assert len(drift["simulated"]) == 1
    simulated = drift["simulated"][0]
    assert simulated["kind"] == "simulated" and simulated["key"] == "monthly_charges_up_20pct"
    assert simulated["title"] == "Monthly charges up 20%"
    assert simulated["note"].startswith("Simulated")
    assert simulated["changed_columns"] == ["MonthlyCharges", "TotalCharges"]
    assert simulated["reference_rows"] == 5634
    assert [f["feature"] for f in simulated["features"]] == [
        "MonthlyCharges", "TotalCharges", "tenure", "Contract",
    ]
    assert simulated["features"][0]["psi_label"] == "major shift"
    assert simulated["prediction_effect"] == {
        "mean_predicted_before": 0.268, "mean_predicted_after": 0.29,
        "share_flagged_before": 0.49, "share_flagged_after": 0.52,
    }


@pytest.mark.parametrize("summary", [None, {"customers": 6}])
def test_missing_monitoring_is_reported_not_invented(summary):
    body = body_of(summary=summary)
    assert body["data_quality"]["available"] is False
    assert "compute_monitoring" in body["data_quality"]["note"]
    assert body["drift"]["available"] is False
    assert body["drift"]["measured"] is None and body["drift"]["simulated"] == []
    assert "compute_monitoring" in body["drift"]["note"]
    # the live sections are unaffected
    assert body["prediction_distribution"]["total"] == 6
    assert body["schema_compatibility"]["compatible"] is True


def test_performance_is_not_verified_without_labeled_new_data():
    performance = body_of()["performance"]
    assert performance["status"] == "not_verified"
    assert performance["labeled_new_data_customers"] == 0
    assert "cannot be verified" in performance["explanation"]


def test_labeled_new_data_is_reported_as_pending_evaluation():
    performance = body_of(labeled_new_data=True)["performance"]
    assert performance["status"] == "pending_evaluation"
    assert performance["labeled_new_data_customers"] == 1
    assert "no performance evaluation" in performance["explanation"]


def test_no_completed_run_returns_404():
    assert make_client(seeded=False).get(URL).status_code == 404


def test_unknown_run_returns_404():
    assert make_client().get(URL, params={"analysis_run_id": 9999}).status_code == 404