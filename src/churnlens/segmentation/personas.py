import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from churnlens.segmentation.summary import priority_tier

K = 5
RANDOM_STATE = 42
HORIZON_MONTHS = 12  # assumption, not a measurement


def fit_segmenter(features, k=K, random_state=RANDOM_STATE):
    """Scale the features, then run K-Means. Returns (pipeline, cluster labels)."""
    pipe = Pipeline([
        ("scale", StandardScaler()),
        ("kmeans", KMeans(n_clusters=k, n_init=10, random_state=random_state)),
    ])
    pipe.fit(features)
    return pipe, pipe.named_steps["kmeans"].labels_


def profile_clusters(df, features, labels):
    """Describe each cluster. Churn labels are used only here, never for clustering."""
    data = features.copy()
    data["cluster"] = labels
    data["Churn"] = df["Churn"].to_numpy()
    data["churned_monthly"] = (df["MonthlyCharges"] * df["Churn"]).to_numpy()

    g = data.groupby("cluster")
    profile = pd.DataFrame({
        "customers": g.size(),
        "churn_rate": g["Churn"].mean(),
        "avg_tenure": g["tenure"].mean(),
        "avg_monthly": g["MonthlyCharges"].mean(),
        "avg_addons": g["n_addons"].mean(),
        "avg_contract_months": g["contract_months"].mean(),
        "pct_fiber": g["internet_fiber"].mean(),
        "pct_dsl": g["internet_dsl"].mean(),
        "churned_monthly_revenue": g["churned_monthly"].sum(),
    })
    profile["share_of_churned_revenue"] = (
        profile["churned_monthly_revenue"] / profile["churned_monthly_revenue"].sum()
    )
    return profile


def name_persona(row):
    """Describe a cluster in words, using only its own averages."""
    if row["pct_fiber"] + row["pct_dsl"] < 0.5:
        return "No-internet customers"

    tenure_word = "Long-tenured" if row["avg_tenure"] >= 48 else "Newer"
    internet_word = "fiber" if row["pct_fiber"] >= row["pct_dsl"] else "DSL"
    if row["avg_contract_months"] < 2:
        contract_word = "month-to-month"
    elif row["avg_contract_months"] < 6:
        contract_word = "short contracts"
    else:
        contract_word = "longer contracts"
    return f"{tenure_word} {internet_word}, {contract_word}"


def assign_names(profile):
    names = profile.apply(name_persona, axis=1)
    if names.duplicated().any():
        raise ValueError(
            "Two clusters got the same persona name; name them by hand: "
            + str(names.to_dict())
        )
    return names


def add_revenue_at_risk(profile, df, labels, probabilities, horizon=HORIZON_MONTHS):
    """Revenue at risk = churn probability x monthly charge x horizon, summed per cluster."""
    labels = np.asarray(labels)
    exposure = (
        np.asarray(probabilities, dtype=float)
        * df["MonthlyCharges"].to_numpy()
        * horizon
    )
    at_risk = pd.Series(exposure).groupby(labels).sum()

    out = profile.copy()
    out["revenue_at_risk_12m"] = at_risk
    out["share_of_revenue_at_risk"] = (
        out["revenue_at_risk_12m"] / out["revenue_at_risk_12m"].sum()
    )
    out["retention_priority"] = (
        out["revenue_at_risk_12m"].rank(ascending=False, method="first").astype(int)
    )
    out["priority_tier"] = out["share_of_revenue_at_risk"].apply(priority_tier)
    return out