MIN_SUPPORT = 0.05

RULES = [
    {
        "code" : "NEW_CUSTOMER",
        "features": ["tenure", "MonthlyCharges", "TotalCharges"],
        "applies": lambda c, t: c["tenure"] <= 12,
        "action": "Contact this newer customer early to check onboarding and satisfaction.",
    },
    {
        "code": "MONTH_TO_MONTH",
        "features": ["Contract"],
        "applies": lambda c, t: c["Contract"] == "Month-to-month",
        "action":"review contract renewal options.", 
    },
    {
        "code": "HIGH_CHARGES",
        "features": ["MonthlyCharges", "InternetService"],
        "applies": lambda c, t: c["MonthlyCharges"] >= t["high_charge"],
        "action": "Investigate billing dissatisfaction or whether the plan fits their needs.",
    },
    {
        "code": "ELECTRONIC_CHECK",
        "features": ["PaymentMethod"],
        "applies": lambda c, t: c["PaymentMethod"] == "Electronic check",
        "action": "Check for payment or billing friction; consider offering automatic payment.",
    },
    {
        "code": "NO_SUPPORT_SERVICES",
        "features": ["TechSupport", "OnlineSecurity"],
        "applies": lambda c, t: (
            c["InternetService"] != "No"
            and c["TechSupport"] == "No"
            and c["OnlineSecurity"] == "No"
        ),
        "action": "Review whether tech support or online security add-ons would help.",
    },
    {
        "code": "HIGH_VALUE_ACCOUNT",
        "features": None,
        "applies": lambda c, t: c["MonthlyCharges"] >= t["high_charge"] and c["tenure"] >= 24,
        "action": "Prioritize this high-value account for personal outreach.",
    },
]

NO_DRIVER_TEXT = (
    "No single rule-based driver stands out; the model flags elevated risk, "
    "so consider general outreach."
)

def customer_reasons(customer, contributions, thresholds, min_support=MIN_SUPPORT,max_reasons=3):
    found = []
    for rule in RULES:
        if not rule["applies"](customer, thresholds):
            continue
        support = None
        if rule["features"] is not None:
            support = float(contributions[rule["features"]].sum())
            if support < min_support:
                continue
        found.append((support, rule))
    found.sort(key=lambda pair: -(pair[0] if pair[0] is not None else 0.0))
    return [
        {"code": rule["code"], "action": rule["action"],
         "support": None if support is None else round(support,3)}
        for support, rule in found[:max_reasons]
    ]

def why_prioritized(rank, prob, monthly_charge, expected_value, offer_cost,success_rate):
    sign = "-" if expected_value < 0 else ""
    return (
        f"Rank {rank}: churn probability {prob:.0%} on ${monthly_charge:,.2f}/month "
        f"gives an expected net value of {sign}${abs(expected_value):,.0f} under the "
        f"assumed ${offer_cost:g} offer cost and {success_rate:.0%} success rate."
    )