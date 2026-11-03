import numpy as np
import pandas as pd
import pytest

from churnlens.explainability.shap_explainer import explain, group_name
from churnlens.features.preprocessing import (
    CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES,
)
from churnlens.models.pipelines import build_pipeline


def make_data(n=300):
    rng = np.random.default_rng(1)
    data = {c: rng.normal(size=n) for c in NUMERIC_FEATURES}
    for c in CATEGORICAL_FEATURES:
        data[c] = rng.choice(["Yes", "No", "Maybe"], size=n)
    X = pd.DataFrame(data)[FEATURES]
    y = pd.Series((data["tenure"] + rng.normal(size=n) < 0).astype(int))
    return X, y


def test_group_name_maps_back_to_original_feature():
    assert group_name("num__tenure") == "tenure"
    assert group_name("cat__Contract_Month-to-month") == "Contract"
    with pytest.raises(ValueError):
        group_name("cat__Mystery_x")


def test_contributions_add_up_to_the_models_score():
    X, y = make_data()
    pipe = build_pipeline("logistic_regression").fit(X, y)
    grouped, baseline = explain(pipe, X, X.iloc[:50])

    assert set(grouped.columns) == set(FEATURES)
    reconstructed = baseline + grouped.sum(axis=1).to_numpy()
    actual = pipe.decision_function(X.iloc[:50])
    assert np.allclose(reconstructed, actual, atol=1e-6)