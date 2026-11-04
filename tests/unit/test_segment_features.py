import pandas as pd
import pytest

from churnlens.segmentation.features import build_segment_features

def make_df():
    return pd.DataFrame({
        "tenure":[1,60],
        "MonthlyCharges": [29.85, 100.0],
        "Contract": ["Month-to-month", "Two year"],
        "InternetService": ["DSL", "Fiber optic"],
        "OnlineSecurity": ["No", "Yes"],
        "OnlineBackup": ["Yes", "Yes"],
        "DeviceProtection": ["No internet service", "Yes"],
        "TechSupport": ["No", "Yes"],
        "StreamingTV": ["No", "Yes"],
        "StreamingMovies": ["No", "No"],
        "Churn": [1, 0],
    })

def test_features_are_computed_correctly():
    out = build_segment_features(make_df())
    assert out["n_addons"].tolist() == [1,5]
    assert out["contract_months"].tolist() == [1,24]
    assert out["internet_dsl"].tolist() == [1,0]
    assert out["internet_fiber"].tolist() == [0,1]

def test_churn_label_is_never_a_feature():
    assert "Churn" not in build_segment_features(make_df()).columns

def test_unknown_contract_is_rejected():
    df = make_df()
    df.loc[0, "Contract"] = "Weekly" 
    with pytest.raises(ValueError):
        build_segment_features(df)