import pandas as pd

from churnlens.explainability.reasons import (
    explanation_text, strength, top_reasons,
)

CONTRIBUTIONS = pd.Series({
    "Contract": 0.8, "tenure": 0.3, "gender": 0.01,
    "InternetService": -0.25, "TechSupport": -0.6, "MonthlyCharges": 0.1,
})
CUSTOMER = pd.Series({
    "Contract": "Month-to-month", "tenure": 3, "gender": "Female",
    "InternetService": "DSL", "TechSupport": "Yes", "MonthlyCharges": 70.5,
})


def test_reasons_are_sorted_and_split_by_direction():
    r = top_reasons(CONTRIBUTIONS, CUSTOMER, n=2)
    assert [x["feature"] for x in r["increasing"]] == ["Contract", "tenure"]
    assert [x["feature"] for x in r["decreasing"]] == ["TechSupport", "InternetService"]


def test_negligible_contributions_are_left_out():
    r = top_reasons(CONTRIBUTIONS, CUSTOMER, n=10)
    all_features = [x["feature"] for x in r["increasing"] + r["decreasing"]]
    assert "gender" not in all_features


def test_strength_words():
    assert strength(0.8) == "strongly"
    assert strength(-0.3) == "moderately"
    assert strength(0.1) == "slightly"


def test_text_mentions_actual_values_and_handles_empty_case():
    text = explanation_text(top_reasons(CONTRIBUTIONS, CUSTOMER))
    assert "Month-to-month" in text and "3 months" in text
    assert explanation_text({"increasing": [], "decreasing": []}) == (
        "No single factor stands out for this customer."
    )