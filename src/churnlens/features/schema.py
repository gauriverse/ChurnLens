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


def dtype_kind(dtype):
    """'numeric', 'text' or 'other' for a pandas dtype name such as 'int64' or 'object'."""
    name = str(dtype).lower()
    if name.rstrip("0123456789") in ("int", "uint", "float"):
        return "numeric"
    if name in ("object", "category") or name.startswith("str"):
        return "text"
    return "other"


def check_schema(columns):
    """Compare a dataset's columns (name -> dtype text) with what the model needs.

    A numeric feature needs an int or float column; a categorical feature needs a text column.
    """
    missing, mismatches = [], []
    for name in FEATURES:
        if name not in columns:
            missing.append(name)
            continue
        expected = "numeric" if name in NUMERIC_FEATURES else "text"
        if dtype_kind(columns[name]) != expected:
            mismatches.append(
                {"column": name, "expected": expected, "found": str(columns[name])}
            )
    known = set(FEATURES) | {ID_COLUMN, TARGET}
    return {
        "compatible": not missing and not mismatches,
        "required_columns": len(FEATURES),
        "missing_columns": missing,
        "type_mismatches": mismatches,
        "extra_columns": [c for c in columns if c not in known],
        "id_column_present": ID_COLUMN in columns,
        "target_column_present": TARGET in columns,
    }