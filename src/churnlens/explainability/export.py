import numpy as np
import pandas as pd

from churnlens.explainability.reasons import describe_value


def top_contributions_long(grouped, X, customer_ids, n=5):
    
    values = grouped.to_numpy()
    columns = np.array(grouped.columns)
    order = np.argsort(-np.abs(values), axis=1)[:, :n]

    rows = []
    for i, customer_id in enumerate(customer_ids):
        for rank, j in enumerate(order[i], start=1):
            feature = columns[j]
            rows.append({
                "customerID": customer_id,
                "rank": rank,
                "feature": feature,
                "feature_value": describe_value(feature, X.iloc[i][feature]),
                "shap_value": round(float(values[i, j]), 4),
            })
    return pd.DataFrame(rows)