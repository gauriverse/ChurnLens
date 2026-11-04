FEATURE_LABELS = {
    "tenure": "tenure",
    "MonthlyCharges": "monthly charges",
    "TotalCharges": "total charges",
    "SeniorCitizen": "senior citizen status",
    "gender": "gender",
    "Partner": "having a partner",
    "Dependents": "having dependents",
    "PhoneService": "phone service",
    "MultipleLines": "multiple lines",
    "InternetService": "internet service",
    "OnlineSecurity": "online security",
    "OnlineBackup": "online backup",
    "DeviceProtection": "device protection",
    "TechSupport": "tech support",
    "StreamingTV": "streaming TV",
    "StreamingMovies": "streaming movies",
    "Contract": "contract type",
    "PaperlessBilling": "paperless billing",
    "PaymentMethod": "payment method",
}

MERGED_FOR_DISPLAY = {
    "tenure and billing": ["tenure", "MonthlyCharges", "TotalCharges"],
}


def merge_for_display(contributions, customer):
    """Combine overlapping features into one factor for the readable text."""
    contributions = contributions.copy()
    customer = customer.copy()
    for label, parts in MERGED_FOR_DISPLAY.items():
        contributions[label] = contributions[parts].sum()
        customer[label] = (
            f"{describe_value('tenure', customer['tenure'])}, "
            f"${float(customer['MonthlyCharges']):,.2f}/month"
        )
        contributions = contributions.drop(parts)
        customer = customer.drop(parts)
    return contributions, customer


def describe_value(feature, value):
    
    if feature == "tenure":
        n = int(value)
        return f"{n} month" if n == 1 else f"{n} months"
    if feature in ("MonthlyCharges", "TotalCharges"):
        return f"${float(value):,.2f}"
    if feature == "SeniorCitizen":
        return "yes" if int(value) == 1 else "no"
    return str(value)


def strength(contribution):
    """Words for the size of a contribution (display cutoffs, not statistics)."""
    size = abs(contribution)
    if size >= 0.5:
        return "strongly"
    if size >= 0.2:
        return "moderately"
    return "slightly"


def _build(series, customer):
    return [
        {
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "value": describe_value(feature, customer[feature]),
            "contribution": round(float(c), 3),
            "strength": strength(c),
        }
        for feature, c in series.items()
    ]


def top_reasons(contributions, customer, n=3, min_size=0.05):
    
    up = contributions[contributions >= min_size].sort_values(ascending=False).head(n)
    down = contributions[contributions <= -min_size].sort_values().head(n)
    return {"increasing": _build(up, customer), "decreasing": _build(down, customer)}


def explanation_text(reasons):
    

    def join(items):
        return "; ".join(
            f"{r['label']} ({r['value']}, {r['strength']})" for r in items
        )

    parts = []
    if reasons["increasing"]:
        parts.append("Factors raising this customer's churn risk score: " + join(reasons["increasing"]) + ".")
    if reasons["decreasing"]:
        parts.append("Factors lowering it: " + join(reasons["decreasing"]) + ".")
    if not parts:
        return "No single factor stands out for this customer."
    return " ".join(parts)