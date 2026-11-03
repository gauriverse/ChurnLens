import numpy as np
import pandas as pd
import pytest

from churnlens.features.preprocessing import (
    CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES,
)
from churnlens.models.pipelines import MODEL_NAMES, build_pipeline


def make_data(n=200):
    rng = np.random.default_rng(0)
    data = {c: rng.normal(size=n) for c in NUMERIC_FEATURES}
    for c in CATEGORICAL_FEATURES:
        data[c] = rng.choice(["Yes", "No"], size=n)
    X = pd.DataFrame(data)[FEATURES]
    y = pd.Series(rng.integers(0, 2, size=n))
    return X, y


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_pipeline_fits_and_returns_valid_probabilities(name):
    X, y = make_data()
    pipe = build_pipeline(name).fit(X, y)
    proba = pipe.predict_proba(X)[:, 1]
    assert proba.shape == (len(X),)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_unknown_model_name_raises():
    with pytest.raises(ValueError):
        build_pipeline("not_a_model")