import pandas as pd

from churnlens.simulator.priority import HORIZON_MONTHS, _check_inputs, expected_value

BASIS = "hypothetical: assumed cost and success rate, not measured outcomes"

def run_scenario(df, name, offer_cost, success_rate, risk_threshold=0.0, max_customers=None, horizon_months=HORIZON_MONTHS, margin=1.0, prob_col="churn_probability", charge_col="MonthlyCharges"):
    _check_inputs(df, prob_col, offer_cost, success_rate)
    if not 0 <= risk_threshold <= 1:
        raise ValueError("risk_threshold must be between 0 and 1")
    if max_customers is not None and max_customers < 0:
        raise ValueError("max_customers cannot be negative")

    eligible = df[df[prob_col] >= risk_threshold].copy()
    eligible["expected_value"] = expected_value(
        eligible[prob_col], eligible[charge_col], offer_cost,
        success_rate, horizon_months, margin,
    )
    eligible = eligible.sort_values("expected_value", ascending=False)
    if max_customers is not None:
        eligible = eligible.head(max_customers)

    cost = len(eligible) * offer_cost
    retained = float((eligible[prob_col] * success_rate).sum())
    preserved = float(
        (eligible[prob_col] * success_rate * eligible[charge_col]
         * horizon_months * margin).sum()
    )
    net = preserved - cost
    return {
        "scenario": name,
        "offer_cost": offer_cost,
        "success_rate": success_rate,
        "risk_threshold": risk_threshold,
        "max_customers": max_customers,
        "customers_targeted": len(eligible),
        "campaign_cost": cost,
        "expected_retained_customers": retained,
        "expected_revenue_preserved": preserved,
        "expected_net_benefit": net,
        "expected_roi": net / cost if cost > 0 else float("nan"),
        "basis": BASIS,
    }

def compare_scenarios(df, scenerios):
    return pd.DataFrame([run_scenario(df, **s) for s in scenerios])