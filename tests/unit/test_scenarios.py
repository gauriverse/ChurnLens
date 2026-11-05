import math

import pandas as pd
import pytest

from churnlens.simulator.scenarios import compare_scenarios, run_scenario

BASE = dict(offer_cost=10, success_rate=0.5)

def make_df():
    return pd.DataFrame({
        "customerID": ["A","B","C"],
        "churn_probability": [0.5,0.2,0.01],
        "MonthlyCharges": [100.0,50.0,40.0],
    })

def test_threshold_scenario_matches_hand_calculation():
    s = run_scenario(make_df(), "t", risk_threshold=0.1, **BASE)
    assert s["customers_targeted"] == 2
    assert s["campaign_cost"] == 20
    assert s["expected_retained_customers"] == pytest.approx(0.35)
    assert s["expected_revenue_preserved"] == pytest.approx(360.0)
    assert s["expected_net_benefit"] == pytest.approx(340.0)
    assert s["expected_roi"] == pytest.approx(17.0)


def test_customer_cap_keeps_best_expected_value_first():
    s = run_scenario(make_df(), "cap", max_customers=1, **BASE)
    assert s["customers_targeted"] == 1
    assert s["expected_net_benefit"] == pytest.approx(290.0)  # customer A only


def test_including_negative_value_customers_lowers_net_benefit():
    broad = run_scenario(make_df(), "broad", risk_threshold=0.0, **BASE)
    narrow = run_scenario(make_df(), "narrow", risk_threshold=0.1, **BASE)
    assert broad["customers_targeted"] == 3
    assert broad["expected_net_benefit"] == pytest.approx(332.4)
    assert broad["expected_net_benefit"] < narrow["expected_net_benefit"]


def test_nobody_eligible_gives_zero_cost_and_nan_roi():
    s = run_scenario(make_df(), "none", risk_threshold=0.99, **BASE)
    assert s["customers_targeted"] == 0
    assert s["campaign_cost"] == 0
    assert math.isnan(s["expected_roi"])


def test_invalid_settings_are_rejected():
    with pytest.raises(ValueError):
        run_scenario(make_df(), "x", risk_threshold=1.5, **BASE)
    with pytest.raises(ValueError):
        run_scenario(make_df(), "x", max_customers=-1, **BASE)
    with pytest.raises(ValueError):
        run_scenario(make_df(), "x", offer_cost=10, success_rate=1.5)


def test_compare_returns_one_row_per_scenario_in_order():
    table = compare_scenarios(make_df(), [
        dict(name="first", risk_threshold=0.1, **BASE),
        dict(name="second", max_customers=1, **BASE),
    ])
    assert table["scenario"].tolist() == ["first", "second"]
    assert (table["basis"].str.startswith("hypothetical")).all()