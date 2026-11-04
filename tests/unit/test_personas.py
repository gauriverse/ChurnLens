import pandas as pd
import pytest

from churnlens.segmentation.personas import (
    add_revenue_at_risk, assign_names, name_persona, priority_tier,
)


def row(**kw):
    base = dict(pct_fiber=0.0, pct_dsl=1.0, avg_tenure=20.0, avg_contract_months=1.0)
    base.update(kw)
    return pd.Series(base)


def test_persona_names_follow_the_rules():
    assert name_persona(row(pct_fiber=1.0, pct_dsl=0.0)) == "Newer fiber, month-to-month"
    assert name_persona(row(avg_contract_months=3.0)) == "Newer DSL, short contracts"
    assert name_persona(row(avg_tenure=60.0, avg_contract_months=20.0)) == "Long-tenured DSL, longer contracts"
    assert name_persona(row(pct_fiber=0.0, pct_dsl=0.0)) == "No-internet customers"


def test_duplicate_names_are_rejected():
    profile = pd.DataFrame([row().to_dict(), row().to_dict()])
    with pytest.raises(ValueError):
        assign_names(profile)


def test_priority_tier_cutoffs():
    assert priority_tier(0.30) == "High"
    assert priority_tier(0.299) == "Medium"
    assert priority_tier(0.10) == "Medium"
    assert priority_tier(0.099) == "Low"


def test_revenue_at_risk_matches_hand_calculation():
    df = pd.DataFrame({"MonthlyCharges": [100.0, 50.0, 10.0]})
    profile = pd.DataFrame(index=[0, 1])
    out = add_revenue_at_risk(profile, df, [0, 0, 1], [0.5, 0.2, 0.1], horizon=12)
    # cluster 0: 0.5*100*12 + 0.2*50*12 = 720; cluster 1: 0.1*10*12 = 12
    assert out.loc[0, "revenue_at_risk_12m"] == pytest.approx(720.0)
    assert out.loc[1, "revenue_at_risk_12m"] == pytest.approx(12.0)
    assert out["retention_priority"].tolist() == [1, 2]
    assert out.loc[0, "share_of_revenue_at_risk"] == pytest.approx(720 / 732)