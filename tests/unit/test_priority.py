import math

import pandas as pd
import pytest

from churnlens.simulator.priority import (
    expected_value, rank_customers, summarize_selection,
)

SETTINGS = dict(offer_cost=10, success_rate=0.5, horizon_months=12, margin=1.0)


def make_df():
    return pd.DataFrame({
        "customerID": ["A", "B", "C"],
        "churn_probability": [0.5, 0.2, 0.01],
        "MonthlyCharges": [100.0, 50.0, 40.0],
    })


def test_expected_value_matches_hand_calculation():
    ev = expected_value([0.5, 0.2, 0.01], [100, 50, 40], 10, 0.5, 12)
    # 0.5*0.5*100*12-10 = 290 ; 0.2*0.5*50*12-10 = 50 ; 0.01*0.5*40*12-10 = -7.6
    assert list(ev.round(2)) == [290.0, 50.0, -7.6]


def test_only_positive_value_customers_are_selected_without_budget():
    ranked = rank_customers(make_df(), **SETTINGS)
    assert ranked["customerID"].tolist() == ["A", "B", "C"]
    assert ranked["selected"].tolist() == [True, True, False]


def test_budget_limits_the_number_of_offers():
    assert rank_customers(make_df(), budget=10, **SETTINGS)["selected"].sum() == 1
    assert rank_customers(make_df(), budget=25, **SETTINGS)["selected"].sum() == 2


def test_value_can_outrank_probability():
    df = pd.DataFrame({
        "customerID": ["cheap_risky", "pricey_less_risky"],
        "churn_probability": [0.6, 0.4],
        "MonthlyCharges": [20.0, 200.0],
    })
    ranked = rank_customers(df, **SETTINGS)
    assert ranked["customerID"].tolist() == ["pricey_less_risky", "cheap_risky"]


def test_summary_matches_hand_calculation():
    ranked = rank_customers(make_df(), **SETTINGS)
    s = summarize_selection(ranked, **SETTINGS)
    assert s["customers_targeted"] == 2
    assert s["campaign_cost"] == 20
    assert s["expected_retained_customers"] == pytest.approx(0.35)
    assert s["expected_revenue_preserved"] == pytest.approx(360.0)
    assert s["expected_net_benefit"] == pytest.approx(340.0)
    assert s["expected_roi"] == pytest.approx(17.0)


def test_invalid_inputs_are_rejected():
    bad = make_df()
    bad.loc[0, "churn_probability"] = 1.5
    with pytest.raises(ValueError):
        rank_customers(bad, **SETTINGS)
    with pytest.raises(ValueError):
        rank_customers(make_df(), offer_cost=0, success_rate=0.5)


def test_roi_is_nan_when_nobody_is_targeted():
    df = pd.DataFrame({"customerID": ["A"], "churn_probability": [0.01],
                       "MonthlyCharges": [10.0]})
    ranked = rank_customers(df, **SETTINGS)
    assert math.isnan(summarize_selection(ranked, **SETTINGS)["expected_roi"])