"""Light helpers shared by the segmentation scripts and the API.

No pandas or scikit-learn here, so the API can import this module cheaply.
"""

HIGH_PRIORITY_SHARE = 0.30    # display cutoffs chosen by the author, not statistical thresholds
MEDIUM_PRIORITY_SHARE = 0.10


def priority_tier(share):
    """High / Medium / Low from a segment's share of 12-month revenue at risk."""
    if share >= HIGH_PRIORITY_SHARE:
        return "High"
    if share >= MEDIUM_PRIORITY_SHARE:
        return "Medium"
    return "Low"


def characteristics(row):
    """Plain-number description of a cluster's averages, for display.

    row is a dict with the profile columns written by build_segments.py.
    """
    fiber, dsl = float(row["pct_fiber"]), float(row["pct_dsl"])
    return {
        "avg_tenure_months": round(float(row["avg_tenure"]), 1),
        "avg_add_on_services": round(float(row["avg_addons"]), 2),
        "avg_contract_months": round(float(row["avg_contract_months"]), 1),
        "share_fiber": round(fiber, 3),
        "share_dsl": round(dsl, 3),
        "share_no_internet": round(max(0.0, 1 - fiber - dsl), 3),
        "share_of_churned_revenue_historical": round(float(row["share_of_churned_revenue"]), 3),
    }