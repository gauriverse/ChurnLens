from collections import Counter

import numpy as np

EPSILON = 1e-4        # floor for empty bins, so the logarithm is defined
PSI_MODERATE = 0.10   # rule-of-thumb cutoffs
PSI_MAJOR = 0.25


def psi(reference_shares, current_shares, epsilon=EPSILON):
    """Population Stability Index between two sets of bin shares."""
    ref = np.asarray(reference_shares, dtype=float)
    cur = np.asarray(current_shares, dtype=float)
    if ref.shape != cur.shape:
        raise ValueError("reference and current need the same number of bins")
    ref = np.clip(ref, epsilon, None)
    cur = np.clip(cur, epsilon, None)
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def psi_label(value):
    if value < PSI_MODERATE:
        return "little or no shift"
    if value < PSI_MAJOR:
        return "moderate shift"
    return "major shift"


def ks_statistic(a, b):
    """Largest gap between the two samples' cumulative distributions (0 = same, 1 = disjoint)."""
    a = np.sort(np.asarray(a, dtype=float))
    b = np.sort(np.asarray(b, dtype=float))
    if len(a) == 0 or len(b) == 0:
        raise ValueError("need at least one value in each sample")
    values = np.concatenate([a, b])
    cdf_a = np.searchsorted(a, values, side="right") / len(a)
    cdf_b = np.searchsorted(b, values, side="right") / len(b)
    return float(np.max(np.abs(cdf_a - cdf_b)))


def shares(counts):
    counts = np.asarray(counts, dtype=float)
    total = counts.sum()
    if total == 0:
        raise ValueError("no values to compare")
    return counts / total


def numeric_edges(reference, n_bins=10):
    """Interior bin edges from the reference's quantiles (repeated edges removed)."""
    reference = np.asarray(reference, dtype=float)
    if len(reference) == 0:
        raise ValueError("need at least one reference value")
    interior = np.linspace(0, 1, n_bins + 1)[1:-1]
    return np.unique(np.quantile(reference, interior))


def bin_counts(values, edges):
    """Count values per bin: first bin is <= edges[0], last bin is > edges[-1]."""
    index = np.searchsorted(edges, np.asarray(values, dtype=float), side="left")
    return np.bincount(index, minlength=len(edges) + 1)


def _rounded(array):
    return [round(float(x), 4) for x in array]


def compare_numeric(reference, current, n_bins=10):
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    edges = numeric_edges(reference, n_bins)
    ref_share = shares(bin_counts(reference, edges))
    cur_share = shares(bin_counts(current, edges))
    value = psi(ref_share, cur_share)
    return {
        "kind": "numeric",
        "psi": round(value, 4),
        "psi_label": psi_label(value),
        "ks_statistic": round(ks_statistic(reference, current), 4),
        "bin_upper_edges": _rounded(edges),   # the last bin is open-ended
        "reference_share": _rounded(ref_share),
        "current_share": _rounded(cur_share),
    }


def compare_categorical(reference, current):
    ref_counts = Counter(str(v) for v in reference)
    cur_counts = Counter(str(v) for v in current)
    categories = sorted(set(ref_counts) | set(cur_counts))
    ref_share = shares([ref_counts.get(c, 0) for c in categories])
    cur_share = shares([cur_counts.get(c, 0) for c in categories])
    value = psi(ref_share, cur_share)
    return {
        "kind": "categorical",
        "psi": round(value, 4),
        "psi_label": psi_label(value),
        "categories": categories,
        "unseen_categories": [c for c in categories if c not in ref_counts],
        "reference_share": _rounded(ref_share),
        "current_share": _rounded(cur_share),
    }


def compare_features(reference, current, numeric_features, categorical_features, n_bins=10):
    """Drift results for every feature, from two DataFrames with the same columns."""
    out = {}
    for column in numeric_features:
        out[column] = compare_numeric(
            reference[column].to_numpy(), current[column].to_numpy(), n_bins
        )
    for column in categorical_features:
        out[column] = compare_categorical(
            reference[column].tolist(), current[column].tolist()
        )
    return out