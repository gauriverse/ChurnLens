import numpy as np
import pandas as pd
import pytest

from churnlens.simulator.scenarios import run_scenario, select_targets, summarize_targets

BASE = dict(offer_cost=10, success_rate=0.5)


def make_df():
    return pd.DataFrame({
        "churn_probability": [0.5, 0.2, 0.01],
        "MonthlyCharges": [100.0, 50.0, 40.0],
        "persona_name": ["X", "X", "Y"],
    })


def test_targets_carry_per_customer_values():
    t = select_targets(make_df(), risk_threshold=0.1, **BASE)
    assert t["persona_name"].tolist() == ["X", "X"]
    assert t["expected_retained"].tolist() == pytest.approx([0.25, 0.1])
    assert t["revenue_preserved"].tolist() == pytest.approx([300.0, 60.0])
    assert t["expected_value"].tolist() == pytest.approx([290.0, 50.0])


def test_expected_value_is_revenue_minus_offer_cost():
    t = select_targets(make_df(), **BASE)  # threshold 0: all three, including a losing one
    assert np.allclose(t["expected_value"], t["revenue_preserved"] - 10)
    assert t["expected_value"].min() == pytest.approx(-7.6)


def test_summary_agrees_with_run_scenario():
    t = select_targets(make_df(), risk_threshold=0.1, **BASE)
    summary = summarize_targets(t, 10)
    assert summary["customers_targeted"] == 2
    assert summary["campaign_cost"] == 20
    assert summary["expected_retained_customers"] == pytest.approx(0.35)
    assert summary["expected_revenue_preserved"] == pytest.approx(360.0)
    assert summary["expected_net_benefit"] == pytest.approx(340.0)
    assert summary["expected_roi"] == pytest.approx(17.0)
    full = run_scenario(make_df(), "S", risk_threshold=0.1, **BASE)
    assert all(full[key] == summary[key] for key in summary)


def test_ties_are_broken_by_input_order():
    df = pd.DataFrame({
        "churn_probability": [0.5, 0.5, 0.5],
        "MonthlyCharges": [100.0, 100.0, 100.0],
        "tag": ["first", "second", "third"],
    })
    assert select_targets(df, max_customers=2, **BASE)["tag"].tolist() == ["first", "second"]


def test_nobody_selected_keeps_the_columns_and_gives_zero_totals():
    t = select_targets(make_df(), risk_threshold=0.99, **BASE)
    assert len(t) == 0
    assert {"expected_retained", "revenue_preserved", "expected_value"} <= set(t.columns)
    summary = summarize_targets(t, 10)
    assert summary["campaign_cost"] == 0 and summary["expected_net_benefit"] == 0
    assert np.isnan(summary["expected_roi"])