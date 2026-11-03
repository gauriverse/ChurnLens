import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from churnlens.evaluation.threshold import sweep_thresholds
from churnlens.models.pipelines import build_pipeline

# Assumptions (NOT measured facts) used to choose the threshold
DEFAULT_COST_SETTINGS = dict(
    offer_cost=40, success_rate=0.30, horizon_months=12, margin=1.0
)
THRESHOLDS = np.round(np.arange(0.05, 0.96, 0.05), 2)


def make_model(random_state=42):
    """Logistic regression pipeline wrapped in sigmoid calibration."""
    base = build_pipeline("logistic_regression", random_state=random_state)
    return CalibratedClassifierCV(base, method="sigmoid", cv=5)


def get_oof_probabilities(X, y, random_state=42):
    """Honest probabilities: each customer is scored by a model that never saw them."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    probs = cross_val_predict(
        make_model(random_state), X, y, cv=cv, method="predict_proba"
    )
    return probs[:, 1]


def pick_threshold(sweep, window=3):
    """Threshold with the best smoothed net benefit (avoids lone lucky spikes)."""
    smoothed = sweep["net_benefit"].rolling(window, center=True, min_periods=1).mean()
    return float(sweep.loc[smoothed.idxmax(), "threshold"])


def train_final(X_train, y_train, cost_settings=None):
    """Return (fitted model, chosen threshold, out-of-fold probabilities, sweep table)."""
    cost_settings = cost_settings or DEFAULT_COST_SETTINGS
    oof = get_oof_probabilities(X_train, y_train)
    sweep = sweep_thresholds(
        y_train, oof, X_train["MonthlyCharges"], THRESHOLDS, **cost_settings
    )
    threshold = pick_threshold(sweep)
    model = make_model().fit(X_train, y_train)
    return model, threshold, oof, sweep