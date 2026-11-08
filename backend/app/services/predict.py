import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.constants import EXPOSURE_HORIZON_MONTHS
from backend.app.models.tables import Customer
from backend.app.services.customer_profile import risk_category_definition
from backend.app.services.model_loader import (
    ModelUnavailable, active_model_version, known_categories, load_artifact,
)
from churnlens.evaluation.risk import risk_category
from churnlens.features.schema import FEATURES

ADD_ON_SERVICES = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]
NO_INTERNET = "No internet service"
NO_PHONE = "No phone service"


class InvalidFeatures(Exception):
    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = problems


def category_problems(features, categories):
    """Values the model never saw in training. A one-hot encoder would silently ignore them."""
    return [
        f"{name}: '{features[name]}' is not a value the model was trained on "
        f"(allowed: {', '.join(allowed)})"
        for name, allowed in categories.items()
        if features[name] not in allowed
    ]


def _warning(text):
    return {"level": "warning", "text": text}


def input_warnings(features, ranges=None):
    """Data-quality notes for one input row, built only from the row and the reference data."""
    notes = []

    for column, (low, high) in (ranges or {}).items():
        value = features[column]
        if value < low or value > high:
            notes.append(_warning(
                f"{column} {value:g} is outside the range seen in the reference data "
                f"({low:g} to {high:g}), so the prediction extrapolates beyond what the "
                "model has seen."
            ))

    has_internet = features["InternetService"] != "No"
    conflicting = [
        name for name in ADD_ON_SERVICES if (features[name] == NO_INTERNET) == has_internet
    ]
    if conflicting:
        verb = "are" if len(conflicting) > 1 else "is"
        notes.append(_warning(
            f"InternetService is '{features['InternetService']}' but "
            f"{', '.join(conflicting)} {verb} inconsistent with it. In the training data "
            f"'{NO_INTERNET}' appears exactly when there is no internet service, so this "
            "combination is unusual and the prediction may be unreliable."
        ))

    if (features["PhoneService"] == "No") != (features["MultipleLines"] == NO_PHONE):
        notes.append(_warning(
            f"PhoneService is '{features['PhoneService']}' but MultipleLines is "
            f"'{features['MultipleLines']}'. In the training data '{NO_PHONE}' appears "
            "exactly when there is no phone service, so this combination is unusual and "
            "the prediction may be unreliable."
        ))

    if features["tenure"] == 0:
        notes.append(_warning(
            "This customer has 0 months of tenure and no billing history, so there is "
            "little behavioural information behind the prediction."
        ))
    return notes


def _pair(low, high):
    return None if low is None or high is None else (float(low), float(high))


def reference_ranges(db: Session, dataset_id):
    """Min and max of the numeric features in the dataset the model was trained on."""
    if dataset_id is None:
        return {}
    row = db.execute(
        select(
            func.min(Customer.tenure), func.max(Customer.tenure),
            func.min(Customer.monthly_charges), func.max(Customer.monthly_charges),
            func.min(Customer.total_charges), func.max(Customer.total_charges),
        ).where(Customer.dataset_id == dataset_id)
    ).one()
    pairs = {
        "tenure": _pair(row[0], row[1]),
        "MonthlyCharges": _pair(row[2], row[3]),
        "TotalCharges": _pair(row[4], row[5]),
    }
    return {name: pair for name, pair in pairs.items() if pair}


def predict_customer(db: Session, features: dict):
    """Score one customer with the active model. Nothing is saved."""
    version = active_model_version(db)
    if version is None or not version.artifact_path:
        raise ModelUnavailable("no active model version with a stored model file")
    artifact = load_artifact(version.artifact_path)
    if list(artifact["features"]) != FEATURES:
        raise ModelUnavailable("the saved model expects different features than this API sends")

    model, threshold = artifact["model"], artifact["threshold"]
    problems = category_problems(features, known_categories(model))
    if problems:
        raise InvalidFeatures(problems)

    frame = pd.DataFrame([features], columns=FEATURES)
    probability = float(model.predict_proba(frame)[0, 1])
    notes = [{"level": "info", "text": "Scored from the values supplied. Nothing is stored."}]
    notes += input_warnings(features, reference_ranges(db, version.training_dataset_id))

    return {
        "model": {
            "name": version.name,
            "version": version.version,
            "algorithm": version.algorithm,
            "decision_threshold": threshold,
            "risk_category_definition": risk_category_definition(threshold),
        },
        "churn_probability": round(probability, 4),
        "risk_category": risk_category(probability, threshold),
        "estimated_revenue_exposure": round(
            probability * features["MonthlyCharges"] * EXPOSURE_HORIZON_MONTHS, 2
        ),
        "notes": notes,
    }