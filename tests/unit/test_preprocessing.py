import numpy as np
import pandas as pd

from churnlens.features.preprocessing import (
    CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, build_preprocessor,
)


def make_X(n=20):
    data = {c: np.arange(n, dtype=float) for c in NUMERIC_FEATURES}
    for c in CATEGORICAL_FEATURES:
        data[c] = ["Yes" if i % 2 == 0 else "No" for i in range(n)]
    return pd.DataFrame(data)[FEATURES]


def test_output_has_no_missing_values():
    out = build_preprocessor().fit_transform(make_X())
    assert not np.isnan(out).any()


def test_unseen_category_does_not_crash():
    X = make_X()
    pre = build_preprocessor().fit(X)
    X_new = X.copy()
    X_new.loc[0, "Contract"] = "Brand new"
    assert pre.transform(X_new).shape[0] == len(X_new)


def test_numeric_columns_are_centred():
    out = build_preprocessor().fit_transform(make_X())
    assert np.allclose(out[:, : len(NUMERIC_FEATURES)].mean(axis=0), 0)