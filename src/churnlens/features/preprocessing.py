from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churnlens.features.schema import (  # noqa: F401
    CATEGORICAL_FEATURES,
    FEATURES,
    ID_COLUMN,
    NUMERIC_FEATURES,
    TARGET,
)

def build_preprocessor():
    """Scale numeric columns and one-hot encode categorical columns"""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0,
    )