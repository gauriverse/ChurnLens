import numpy as np
import pandas as pd

from churnlens.data.splitting import split_data
from churnlens.features.preprocessing import (
    CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, TARGET,
)


def make_df(n=200):
    data = {c: np.arange(n, dtype=float) for c in NUMERIC_FEATURES}
    for c in CATEGORICAL_FEATURES:
        data[c] = ["Yes" if i % 2 == 0 else "No" for i in range(n)]
    data[TARGET] = [1 if i % 4 == 0 else 0 for i in range(n)]
    return pd.DataFrame(data)


def test_split_sizes_and_churn_rate_are_preserved():
    X_train, X_test, y_train, y_test = split_data(make_df())
    assert len(X_train) == 160 and len(X_test) == 40
    assert y_train.mean() == 0.25 and y_test.mean() == 0.25


def test_train_and_test_do_not_overlap():
    X_train, X_test, _, _ = split_data(make_df())
    assert set(X_train.index).isdisjoint(set(X_test.index))
    assert list(X_train.columns) == FEATURES