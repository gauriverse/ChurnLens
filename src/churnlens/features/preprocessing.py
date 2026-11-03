from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ID_COLUMN = "customerID"
TARGET = "Churn"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]

CATEGORICAL_FEATURES = [
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "Contract",
    "PaperlessBilling", "PaymentMethod",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

def build_preprocessor():
    """Scale numeric columns and one-hot encode categorical columns"""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0,
    )