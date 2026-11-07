import numpy as np
import pandas as pd
import pytest

from churnlens.monitoring.drift import (
    bin_counts, compare_categorical, compare_features, compare_numeric,
    ks_statistic, numeric_edges, psi, psi_label,
)


def test_psi_matches_hand_calculation():
    # (0.25-0.5)*ln(0.25/0.5) + (0.75-0.5)*ln(0.75/0.5) = 0.1733 + 0.1014
    assert psi([0.5, 0.5], [0.25, 0.75]) == pytest.approx(0.2747, abs=1e-4)


def test_psi_of_identical_distributions_is_zero():
    assert psi([0.2, 0.3, 0.5], [0.2, 0.3, 0.5]) == 0.0


def test_psi_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        psi([0.5, 0.5], [1.0])


def test_psi_label_cutoffs():
    assert psi_label(0.0999) == "little or no shift"
    assert psi_label(0.1) == "moderate shift"
    assert psi_label(0.2499) == "moderate shift"
    assert psi_label(0.25) == "major shift"


def test_ks_statistic_hand_values():
    assert ks_statistic([1, 2, 3, 4], [3, 4, 5, 6]) == pytest.approx(0.5)
    assert ks_statistic([1, 2, 3], [1, 2, 3]) == 0.0
    assert ks_statistic([1, 2], [3, 4]) == 1.0


def test_ks_rejects_empty_samples():
    with pytest.raises(ValueError):
        ks_statistic([], [1, 2])


def test_bin_edges_and_counts():
    reference = np.arange(1, 101)
    edges = numeric_edges(reference, n_bins=4)
    assert edges.tolist() == pytest.approx([25.75, 50.5, 75.25])
    assert bin_counts(reference, edges).tolist() == [25, 25, 25, 25]
    # values beyond the reference range fall into the first and last bins
    assert bin_counts([-5, 1000], edges).tolist() == [1, 0, 0, 1]


def test_compare_numeric_identical_and_shifted():
    reference = np.arange(1, 101)
    same = compare_numeric(reference, reference, n_bins=4)
    assert same["psi"] == 0.0 and same["ks_statistic"] == 0.0
    assert same["psi_label"] == "little or no shift"
    assert same["reference_share"] == [0.25, 0.25, 0.25, 0.25]

    shifted = compare_numeric(reference, reference + 50, n_bins=4)
    assert shifted["ks_statistic"] == pytest.approx(0.5)
    assert shifted["psi_label"] == "major shift"
    assert shifted["current_share"] == [0.0, 0.0, 0.25, 0.75]
    assert shifted["bin_upper_edges"] == [25.75, 50.5, 75.25]


def test_compare_categorical_with_unseen_category():
    reference = ["a"] * 50 + ["b"] * 50
    current = ["a"] * 25 + ["b"] * 70 + ["c"] * 5
    out = compare_categorical(reference, current)
    assert out["categories"] == ["a", "b", "c"]
    assert out["unseen_categories"] == ["c"]
    assert out["reference_share"] == [0.5, 0.5, 0.0]
    assert out["current_share"] == [0.25, 0.7, 0.05]
    assert out["psi_label"] == "major shift"


def test_compare_features_covers_every_requested_column():
    train = pd.DataFrame({"x": np.arange(100), "kind": ["a", "b"] * 50})
    out = compare_features(train, train, ["x"], ["kind"])
    assert list(out) == ["x", "kind"]
    assert out["x"]["kind"] == "numeric" and out["kind"]["kind"] == "categorical"
    assert out["x"]["psi"] == 0.0 and out["kind"]["psi"] == 0.0