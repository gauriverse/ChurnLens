from backend.app.services.model_health import (
    build_performance, feature_rows, schema_explanation,
)


def result(psi):
    return {
        "kind": "numeric", "psi": psi, "psi_label": "x", "ks_statistic": 0.1,
        "bin_upper_edges": [1.0], "reference_share": [0.5, 0.5], "current_share": [0.5, 0.5],
    }


def test_feature_rows_are_sorted_by_psi_then_name():
    rows = feature_rows({"b": result(0.1), "a": result(0.1), "c": result(0.3), "d": result(0.0)})
    assert [r["feature"] for r in rows] == ["c", "a", "b", "d"]
    assert rows[0]["psi"] == 0.3


def test_schema_explanation_wording():
    ok = {"compatible": True, "required_columns": 19, "missing_columns": [], "type_mismatches": []}
    assert schema_explanation(ok) == (
        "All 19 features the model requires are present with compatible types."
    )
    bad = {
        "compatible": False, "required_columns": 19,
        "missing_columns": ["Contract", "tenure"],
        "type_mismatches": [{"column": "TotalCharges", "expected": "numeric", "found": "object"}],
    }
    text = schema_explanation(bad)
    assert "missing columns: Contract, tenure" in text
    assert "incompatible types: TotalCharges" in text
    assert "retraining" in text


def test_performance_states():
    assert build_performance(0)["status"] == "not_verified"
    assert "cannot be verified" in build_performance(0)["explanation"]
    pending = build_performance(3)
    assert pending["status"] == "pending_evaluation"
    assert "3 customers" in pending["explanation"]
    assert "no performance evaluation" in pending["explanation"]