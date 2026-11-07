import pandas as pd


def missing_mask(df):
    """True where a value is missing. Blank or whitespace-only text counts as missing."""
    blank = df.astype(str).apply(lambda column: column.str.strip() == "")
    return df.isna() | blank


def completeness_report(df):
    """Missing values per column and the share of fully complete rows."""
    n = len(df)
    if n == 0:
        raise ValueError("empty dataset")
    mask = missing_mask(df)
    per_column = [
        {
            "column": str(c),
            "missing": int(mask[c].sum()),
            "missing_pct": round(100 * int(mask[c].sum()) / n, 2),
        }
        for c in df.columns
    ]
    complete = int((~mask.any(axis=1)).sum())
    return {
        "rows": n,
        "columns": len(df.columns),
        "complete_rows": complete,
        "complete_rows_pct": round(100 * complete / n, 2),
        "columns_with_missing": [c for c in per_column if c["missing"] > 0],
        "per_column": per_column,
    }