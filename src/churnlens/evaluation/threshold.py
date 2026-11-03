import numpy as np
import pandas as pd


def campaign_outcome(y_true, y_prob, monthly_charges, threshold,
                     offer_cost, success_rate, horizon_months=12, margin=1.0):
    """Replay a retention campaign on historical labels.

    Customers with probability >= threshold get an offer.
    Each offer costs `offer_cost`. If the customer really churned, the offer
    saves them with probability `success_rate`, preserving
    monthly_charges * horizon_months * margin of revenue.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    charges = np.asarray(monthly_charges, dtype=float)

    targeted = y_prob >= threshold
    churners_reached = targeted & (y_true == 1)

    n_targeted = int(targeted.sum())
    campaign_cost = n_targeted * offer_cost
    retained = float(churners_reached.sum()) * success_rate
    revenue_preserved = float(
        (charges[churners_reached] * horizon_months * margin * success_rate).sum()
    )
    net_benefit = revenue_preserved - campaign_cost
    roi = net_benefit / campaign_cost if campaign_cost > 0 else float("nan")

    return {
        "threshold": threshold,
        "targeted": n_targeted,
        "churners_reached": int(churners_reached.sum()),
        "campaign_cost": campaign_cost,
        "estimated_retained": retained,
        "revenue_preserved": revenue_preserved,
        "net_benefit": net_benefit,
        "roi": roi,
    }


def sweep_thresholds(y_true, y_prob, monthly_charges, thresholds, **kwargs):
    """Run campaign_outcome for many thresholds and return a table."""
    rows = [
        campaign_outcome(y_true, y_prob, monthly_charges, t, **kwargs)
        for t in thresholds
    ]
    return pd.DataFrame(rows)