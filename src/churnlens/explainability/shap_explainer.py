import numpy as np
import pandas as pd
import shap

from churnlens.features.preprocessing import CATEGORICAL_FEATURES

def group_name(column_name):
    if column_name.startswith("num__"):
        return column_name[len("num__"):]
    for feature in CATEGORICAL_FEATURES:
        if column_name.startswith(f"cat__{feature}_"):
            return feature
    raise ValueError(f"Cannot map column to a feature: {column_name}")


def explain(pipeline, X_background, X_explain):
    prep = pipeline.named_steps["prep"]
    model = pipeline.named_steps["model"]

    background = prep.transform(X_background)
    to_explain = prep.transform(X_explain)

    # Use ALL background rows so the baseline is exact and reproducible
    masker = shap.maskers.Independent(background, max_samples=background.shape[0])
    explainer = shap.LinearExplainer(model, masker)
    explanation = explainer(to_explain)

    values = explanation.values
    baseline = float(np.asarray(explanation.base_values).ravel()[0])

    encoded_names = prep.get_feature_names_out()
    wide = pd.DataFrame(values, columns=encoded_names, index=X_explain.index)

    groups = [group_name(n) for n in encoded_names]
    grouped = wide.T.groupby(groups).sum().T
    return grouped, baseline