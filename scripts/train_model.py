import json

import joblib
import pandas as pd
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)

from churnlens.evaluation.threshold import campaign_outcome
from churnlens.features.preprocessing import FEATURES, TARGET
from churnlens.models.train import DEFAULT_COST_SETTINGS, train_final

VERSION = "v1"

train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")
X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

# 1. Everything is decided using the training data only
model, threshold, oof, sweep = train_final(X_train, y_train)

# 2. The single evaluation on the sealed test set
p_test = model.predict_proba(X_test)[:, 1]
pred = (p_test >= threshold).astype(int)
tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()

metrics = {
    "model_version": VERSION,
    "algorithm": "logistic_regression + sigmoid calibration",
    "training_rows": len(train),
    "test_rows": len(test),
    "threshold": threshold,
    "cost_assumptions": DEFAULT_COST_SETTINGS,
    "cv_train": {
        "roc_auc": round(roc_auc_score(y_train, oof), 3),
        "brier": round(brier_score_loss(y_train, oof), 3),
    },
    "test": {
        "roc_auc": round(roc_auc_score(y_test, p_test), 3),
        "pr_auc": round(average_precision_score(y_test, p_test), 3),
        "brier": round(brier_score_loss(y_test, p_test), 3),
        "mean_predicted": round(p_test.mean(), 3),
        "actual_churn_rate": round(y_test.mean(), 3),
        "precision": round(precision_score(y_test, pred), 3),
        "recall": round(recall_score(y_test, pred), 3),
        "f1": round(f1_score(y_test, pred), 3),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    },
    "test_campaign_at_threshold": campaign_outcome(
        y_test, p_test, X_test["MonthlyCharges"], threshold, **DEFAULT_COST_SETTINGS
    ),
    "test_campaign_contact_everyone": campaign_outcome(
        y_test, p_test, X_test["MonthlyCharges"], 0.0, **DEFAULT_COST_SETTINGS
    ),
}

# 3. Save the outputs
joblib.dump(
    {"model": model, "threshold": threshold, "features": FEATURES, "version": VERSION},
    f"artifacts/churn_model_{VERSION}.joblib",
)
with open(f"artifacts/metrics_{VERSION}.json", "w") as f:
    json.dump(metrics, f, indent=2, default=float)

# Predictions for every customer, each one out-of-sample
preds = pd.concat([
    pd.DataFrame({"customerID": train["customerID"], "churn_probability": oof,
                  "prediction_source": "out_of_fold_train"}),
    pd.DataFrame({"customerID": test["customerID"], "churn_probability": p_test,
                  "prediction_source": "holdout_test"}),
]).reset_index(drop=True)
preds.to_csv(f"data/processed/predictions_{VERSION}.csv", index=False)

print(json.dumps(metrics, indent=2, default=float))
print("predictions saved:", len(preds), "rows")