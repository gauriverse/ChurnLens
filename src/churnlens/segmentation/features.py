import pandas as pd

ADDON_COLUMNS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]
CONTRACT_MONTHS = {"Month-to-month": 1, "One year": 12, "Two year": 24}

def build_segment_features(df):
    out = pd.DataFrame(index=df.index)
    out["tenure"] = df["tenure"]
    out["MonthlyCharges"] = df["MonthlyCharges"]
    out["n_addons"] = (df[ADDON_COLUMNS] == "Yes").sum(axis=1)
    out["contract_months"] = df["Contract"].map(CONTRACT_MONTHS)
    out["internet_dsl"] = (df["InternetService"] == "DSL").astype(int)
    out["internet_fiber"] = (df["InternetService"] == "Fiber optic").astype(int)

    if out.isna().any().any():
        raise ValueError("Segment features contain missing values")
    return out