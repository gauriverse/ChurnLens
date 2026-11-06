import numpy as np
from lifelines import KaplanMeierFitter

DEFAULT_MILESTONES = (12, 24, 48, 72)


def km_summary(durations, events, horizon=72, milestones=DEFAULT_MILESTONES):
    """Kaplan-Meier summary for one group of customers.

    durations: months observed (whole months, greater than 0)
    events: 1 if the customer churned, 0 if still active (right-censored)
    """
    durations = np.asarray(durations, dtype=float)
    events = np.asarray(events, dtype=int)
    if len(durations) == 0:
        raise ValueError("need at least one customer")
    if len(durations) != len(events):
        raise ValueError("durations and events must have the same length")
    if (durations <= 0).any():
        raise ValueError("durations must be greater than 0; drop customers with no observed time first")

    # Never extrapolate beyond the longest observed tenure
    last_month = int(min(horizon, durations.max()))
    km = KaplanMeierFitter().fit(durations, event_observed=events)
    months = np.arange(0, last_month + 1)
    survival = km.survival_function_at_times(months).to_numpy()

    return {
        "customers": int(len(durations)),
        "events": int(events.sum()),
        "horizon_months": last_month,
        # whole-month data: area under the step curve = sum of S(m) at the start of each month
        "expected_active_months": round(float(survival[:-1].sum()), 2),
        "survival_at": {
            str(m): round(float(survival[m]), 4) for m in milestones if m <= last_month
        },
        "points": [
            {"month": int(m), "survival": round(float(s), 4)}
            for m, s in zip(months, survival)
        ],
    }


def km_by_group(df, group_col, all_label, duration_col="tenure", event_col="churned",
                min_customers=30, **kwargs):
    """One summary for everyone plus one per group value.

    Customers with no observed time or an unknown outcome are dropped. Groups
    smaller than min_customers are left out because their curves would be noise.
    """
    usable = df[(df[duration_col] > 0) & df[event_col].notna()]
    groups = {
        all_label: km_summary(usable[duration_col], usable[event_col].astype(int), **kwargs)
    }
    for name, part in usable.groupby(group_col):
        if len(part) >= min_customers:
            groups[str(name)] = km_summary(
                part[duration_col], part[event_col].astype(int), **kwargs
            )
    return groups