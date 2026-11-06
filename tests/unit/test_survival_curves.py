import pandas as pd
import pytest

from churnlens.survival.curves import km_by_group, km_summary


def test_no_censoring_matches_hand_calculation():
    # Three customers leave at months 1, 2 and 3: survival is 1, 2/3, 1/3, 0
    out = km_summary([1, 2, 3], [1, 1, 1], horizon=3)
    assert [p["survival"] for p in out["points"]] == [1.0, 0.6667, 0.3333, 0.0]
    assert out["expected_active_months"] == pytest.approx(2.0)  # 1 + 2/3 + 1/3
    assert out["customers"] == 3 and out["events"] == 3 and out["horizon_months"] == 3
    assert out["survival_at"] == {}  # default milestones are beyond the observed window

    shorter = km_summary([1, 2, 3], [1, 1, 1], horizon=2)
    assert shorter["horizon_months"] == 2
    assert shorter["expected_active_months"] == pytest.approx(1.67, abs=0.01)


def test_censored_customers_are_not_counted_as_churn():
    # Months 2 and 4 are still-active customers. S(1)=0.75, S(3)=0.75*0.5=0.375
    out = km_summary([1, 2, 3, 4], [1, 0, 1, 0], horizon=4)
    assert [p["survival"] for p in out["points"]] == [1.0, 0.75, 0.75, 0.375, 0.375]
    assert out["events"] == 2
    assert out["expected_active_months"] == pytest.approx(2.875, abs=0.01)  # 1+0.75+0.75+0.375


def test_milestones_are_reported_only_inside_the_observed_window():
    out = km_summary([1, 2, 3], [1, 1, 1], horizon=3, milestones=(1, 2, 3, 12))
    assert out["survival_at"] == {"1": 0.6667, "2": 0.3333, "3": 0.0}


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        km_summary([0, 1], [1, 0])      # zero months observed
    with pytest.raises(ValueError):
        km_summary([], [])


def test_group_summaries_drop_unusable_rows():
    df = pd.DataFrame({
        "tenure": [1, 2, 3, 4, 0, 5],
        "churned": [True, False, True, False, True, None],
        "contract": ["A", "A", "A", "A", "A", "B"],
    })
    # the tenure-0 row and the unknown-outcome row are dropped, leaving the 4 customers above
    out = km_by_group(df, "contract", "All", min_customers=1)
    assert list(out) == ["All", "A"]
    assert out["All"]["customers"] == 4 and out["All"]["events"] == 2
    assert out["A"]["expected_active_months"] == pytest.approx(2.875, abs=0.01)


def test_small_groups_are_omitted():
    df = pd.DataFrame({
        "tenure": [1, 2, 3, 4, 1, 2],
        "churned": [True, False, True, False, True, True],
        "contract": ["A", "A", "A", "A", "B", "B"],
    })
    assert list(km_by_group(df, "contract", "All", min_customers=3)) == ["All", "A"]