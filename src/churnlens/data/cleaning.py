import pandas as pd


def load_raw(path):
    """Read the raw Telco CSV into a DataFrame."""
    return pd.read_csv(path)


def clean_telco(df):
    """Return a cleaned copy of the raw Telco DataFrame."""
    df = df.copy()  

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()


    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

   
    new_customers = df["tenure"] == 0
    df.loc[new_customers & df["TotalCharges"].isna(), "TotalCharges"] = 0.0

    
    if df["TotalCharges"].isna().any():
        raise ValueError("TotalCharges still has missing values after cleaning")

    
    df["Churn"] = (df["Churn"] == "Yes").astype(int)

    
    if df["customerID"].duplicated().any():
        raise ValueError("Duplicate customerID values found")

    return df