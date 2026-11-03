from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from churnlens.features.preprocessing import build_preprocessor

MODEL_NAMES = ["dummy","logistic_regression","random_forest","xgboost"]

def build_pipeline(name, scale_pos_weight=1.0, random_state=42):
    if name == "dummy":
        model = DummyClassifier(strategy="prior")
    elif name == "logistic_regression":
        model = LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=random_state
        )
    elif name == "random_forest":
        model = RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=random_state,
        )
    elif name == "xgboost":
        model = XGBClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, scale_pos_weight=scale_pos_weight, eval_metric="logloss", n_jobs=-1, random_state=random_state,
        )
    else:
        raise ValueError(f"Unknown model name: {name}")

    return Pipeline([("prep", build_preprocessor()), ("model", model)])