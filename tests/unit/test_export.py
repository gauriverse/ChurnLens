import pandas as pd

from churnlens.explainability.export import top_contributions_long


def test_keeps_largest_by_absolute_size_with_ranks():
    grouped = pd.DataFrame({
        "Contract": [0.8, -0.1],
        "tenure": [-0.9, 0.05],
        "gender": [0.01, 0.6],
    })
    X = pd.DataFrame({
        "Contract": ["Month-to-month", "Two year"],
        "tenure": [3, 60],
        "gender": ["Female", "Male"],
    })
    out = top_contributions_long(grouped, X, ["A", "B"], n=2)

    assert len(out) == 4
    first = out[out["customerID"] == "A"]
    assert first["feature"].tolist() == ["tenure", "Contract"]
    assert first["rank"].tolist() == [1, 2]
    assert first["shap_value"].tolist() == [-0.9, 0.8]
    assert first["feature_value"].tolist() == ["3 months", "Month-to-month"]