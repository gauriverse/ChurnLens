import pandas as pd

from churnlens.simulator.recommendations import customer_reasons, why_prioritized

FEATURES = ["tenure", "MonthlyCharges", "TotalCharges", "Contract",
            "PaymentMethod", "InternetService", "TechSupport", "OnlineSecurity"]
THRESHOLDS = {"high_charge": 90.0}


def contributions(**kw):
    base = {f: 0.0 for f in FEATURES}
    base.update(kw)
    return pd.Series(base)

def customer(**kw):
    base = dict(tenure=30, MonthlyCharges=50.0, Contract="Two year", PaymentMethod="Credit card (automatic)", InternetService="DSL", TechSupport="Yes", OnlineSecurity="Yes")
    base.update(kw)
    return pd.Series(base)

def test_matching_rules_are_returned_strongest_support_first():
    c = customer(tenure=3, Contract="Month-to-month")
    contrib = contributions(tenure=1.0, MonthlyCharges=-0.2, TotalCharges=0.1, Contract=0.4)
    codes = [r["code"] for r in customer_reasons(c, contrib, THRESHOLDS)]
    assert codes == ["NEW_CUSTOMER", "MONTH_TO_MONTH"]


def test_rule_is_dropped_when_the_model_does_not_support_it():
    c = customer(Contract="Month-to-month")
    contrib = contributions(Contract=-0.3)
    assert customer_reasons(c, contrib, THRESHOLDS) == []


def test_high_value_account_needs_no_model_support():
    c = customer(MonthlyCharges=100.0, tenure=30)
    codes = [r["code"] for r in customer_reasons(c, contributions(), THRESHOLDS)]
    assert codes == ["HIGH_VALUE_ACCOUNT"]


def test_customers_without_internet_never_get_the_support_services_rule():
    c = customer(InternetService="No", TechSupport="No internet service",
                 OnlineSecurity="No internet service")
    contrib = contributions(TechSupport=0.5, OnlineSecurity=0.5)
    assert customer_reasons(c, contrib, THRESHOLDS) == []


def test_max_reasons_limits_the_list():
    c = customer(tenure=3, Contract="Month-to-month", PaymentMethod="Electronic check")
    contrib = contributions(tenure=1.0, Contract=0.4, PaymentMethod=0.3)
    assert len(customer_reasons(c, contrib, THRESHOLDS, max_reasons=2)) == 2


def test_why_prioritized_sentence():
    text = why_prioritized(1, 0.816, 105.0, 268.283, 40, 0.3)
    assert text == (
        "Rank 1: churn probability 82% on $105.00/month gives an expected net "
        "value of $268 under the assumed $40 offer cost and 30% success rate."
    )