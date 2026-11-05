import numpy as np
import pandas as pd

HORIZON_MONTHS = 12


def expected_value(prob, monthly_charges, offer_cost, success_rate,
                   horizon_months=HORIZON_MONTHS, margin=1.0):
    """Expected net benefit of contacting each customer (revenue, not profit)."""
    prob = np.asarray(prob, dtype=float)
    charges = np.asarray(monthly_charges, dtype=float)
    return prob * success_rate * charges * horizon_months * margin - offer_cost


def _check_inputs(df, prob_col, offer_cost, success_rate):
    if offer_cost <= 0:
        raise ValueError("offer_cost must be positive")
    if not 0 <= success_rate <= 1:
        raise ValueError("success_rate must be between 0 and 1")
    if df[prob_col].isna().any() or not df[prob_col].between(0, 1).all():
        raise ValueError("probabilities must be between 0 and 1 with no missing values")


def rank_customers(df, offer_cost, success_rate, budget=None,
                   horizon_months=HORIZON_MONTHS, margin=1.0,
                   prob_col="churn_probability", charge_col="MonthlyCharges"):
    """Rank customers by expected value and mark who gets an offer."""
    _check_inputs(df, prob_col, offer_cost, success_rate)
    out = df.copy()
    out["expected_value"] = expected_value(
        out[prob_col], out[charge_col], offer_cost, success_rate, horizon_months, margin
    )
    out["priority_rank"] = (
        out["expected_value"].rank(ascending=False, method="first").astype(int)
    )
    max_offers = len(out) if budget is None else int(budget // offer_cost)
    out["selected"] = (out["priority_rank"] <= max_offers) & (out["expected_value"] > 0)
    return out.sort_values("priority_rank")


def summarize_selection(ranked, offer_cost, success_rate,
                        horizon_months=HORIZON_MONTHS, margin=1.0,
                        prob_col="churn_probability", charge_col="MonthlyCharges"):
    """Expected outcome of the campaign. Hypothetical: depends on the assumptions."""
    chosen = ranked[ranked["selected"]]
    cost = len(chosen) * offer_cost
    retained = float((chosen[prob_col] * success_rate).sum())
    preserved = float(
        (chosen[prob_col] * success_rate * chosen[charge_col]
         * horizon_months * margin).sum()
    )
    net = preserved - cost
    return {
        "customers_targeted": len(chosen),
        "campaign_cost": cost,
        "expected_retained_customers": retained,
        "expected_revenue_preserved": preserved,
        "expected_net_benefit": net,
        "expected_roi": net / cost if cost > 0 else float("nan"),
    }