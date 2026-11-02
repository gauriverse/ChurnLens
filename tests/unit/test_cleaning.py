import pandas as pd
from churnlens.data.cleaning import clean_telco


def make_df():
    return pd.DataFrame({
        "customerID": ["A", "B"],
        "tenure": [0, 12],
        "TotalCharges": [" ", "500.5"],
        "Churn": ["No", "Yes"],
    })


def test_blank_total_charges_become_zero_for_new_customers():
    out = clean_telco(make_df())
    assert out.loc[0, "TotalCharges"] == 0.0


def test_churn_becomes_binary():
    out = clean_telco(make_df())
    assert out["Churn"].tolist() == [0, 1]