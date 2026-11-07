import pandas as pd

from churnlens.simulator.priority import HORIZON_MONTHS, _check_inputs, expected_value

BASIS = "hypothetical: assumed cost and success rate, not measured outcomes"

def select_targets(df, offer_cost, success_rate, risk_threshold=0.0, max_customers=None,
                   horizon_months=HORIZON_MONTHS, margin=1.0,
                   prob_col="churn_probability", charge_col="MonthlyCharges"):
    
    _check_inputs(df, prob_col, offer_cost, success_rate)
    if not 0 <= risk_threshold <= 1:
        raise ValueError("risk_threshold must be between 0 and 1")
    if max_customers is not None and max_customers < 0:
        raise ValueError("max_customers cannot be negative")

    targets = df[df[prob_col] >= risk_threshold].copy()
    targets["expected_retained"] = targets[prob_col] * success_rate
    targets["revenue_preserved"] = (
        targets["expected_retained"] * targets[charge_col] * horizon_months * margin
    )
    targets["expected_value"] = expected_value(
        targets[prob_col], targets[charge_col], offer_cost, success_rate, horizon_months, margin
    )
    targets = targets.sort_values("expected_value", ascending=False, kind="mergesort")
    if max_customers is not None:
        targets = targets.head(max_customers)
    return targets

def summarize_targets(targets, offer_cost):
    n = len(targets)
    cost = n * offer_cost
    preserved = float(targets["revenue_preserved"].sum())
    net = preserved - cost
    return {
        "customers_targeted": n,
        "campaign_cost": cost,
        "expected_retained_customers": float(targets["expected_retained"].sum()),
        "expected_revenue_preserved": preserved,
        "expected_net_benefit": net,
        "expected_roi": net / cost if cost > 0 else float("nan"),
    }

def run_scenario(df, name, offer_cost, success_rate, risk_threshold=0.0, max_customers=None,
                 horizon_months=HORIZON_MONTHS, margin=1.0,
                 prob_col="churn_probability", charge_col="MonthlyCharges"):
    
    targets = select_targets(
        df, offer_cost=offer_cost, success_rate=success_rate, risk_threshold=risk_threshold,
        max_customers=max_customers, horizon_months=horizon_months, margin=margin,
        prob_col=prob_col, charge_col=charge_col,
    )
    return {
        "scenario": name,
        "offer_cost": offer_cost,
        "success_rate": success_rate,
        "risk_threshold": risk_threshold,
        "max_customers": max_customers,
        **summarize_targets(targets, offer_cost),
        "basis": BASIS,
    }


def compare_scenarios(df, scenarios):
    return pd.DataFrame([run_scenario(df, **s) for s in scenarios])