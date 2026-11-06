HIGH_RISK_CUTOFF = 0.5


def risk_category(probability, threshold, high_cutoff=HIGH_RISK_CUTOFF):
    if not 0 <= threshold <= high_cutoff <= 1:
        raise ValueError("need 0 <= threshold <= high_cutoff <= 1")
    if probability >= high_cutoff:
        return "High"
    if probability >= threshold:
        return "Medium"
    return "Low"