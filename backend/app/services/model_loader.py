import threading
from pathlib import Path

import joblib
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.tables import ModelVersion
from churnlens.features.schema import CATEGORICAL_FEATURES

PROJECT_ROOT = Path(__file__).resolve().parents[3]

_lock = threading.Lock()
_cache = {}


class ModelUnavailable(Exception):
    """No usable trained model: none is active, or its file cannot be used."""


def active_model_version(db: Session):
    """The model version marked active (the newest one if several are)."""
    return db.scalar(
        select(ModelVersion)
        .where(ModelVersion.is_active.is_(True))
        .order_by(ModelVersion.id.desc())
        .limit(1)
    )


def load_artifact(artifact_path):
    """Load a saved model the first time it is needed, then reuse it for every request.

    Only load files this project wrote itself: joblib files are Python pickles, and
    loading an untrusted one can run arbitrary code.
    """
    path = Path(artifact_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    key = str(path)
    if key not in _cache:
        with _lock:
            if key not in _cache:  # another request may have finished loading while we waited
                if not path.is_file():
                    raise ModelUnavailable(f"model file not found: {artifact_path}")
                try:
                    _cache[key] = joblib.load(path)
                except Exception as error:
                    raise ModelUnavailable(
                        f"model file could not be loaded ({type(error).__name__}); "
                        "it may have been saved with a different scikit-learn version"
                    ) from error
    return _cache[key]


def clear_model_cache():
    with _lock:
        _cache.clear()


def fitted_pipeline(model):
    """The fitted preprocessing + classifier pipeline inside a (possibly calibrated) model."""
    calibrated = getattr(model, "calibrated_classifiers_", None)
    return calibrated[0].estimator if calibrated else model


def known_categories(model):
    """Allowed values for each categorical feature, read from the fitted one-hot encoder."""
    encoder = fitted_pipeline(model).named_steps["prep"].named_transformers_["cat"]
    return {
        name: [str(value) for value in values]
        for name, values in zip(CATEGORICAL_FEATURES, encoder.categories_)
    }