import pandas as pd
import pytest

from churnlens.data.quality import completeness_report, missing_mask


def test_missing_values_and_blank_text_are_counted():
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", " ", "z"], "c": [1, 2, 3]})
    assert missing_mask(df).sum().to_dict() == {"a": 1, "b": 1, "c": 0}

    report = completeness_report(df)
    assert report["rows"] == 3 and report["columns"] == 3
    assert report["complete_rows"] == 2            # row 1 has both problems, rows 0 and 2 are clean
    assert report["complete_rows_pct"] == pytest.approx(66.67, abs=0.01)
    by_column = {c["column"]: c for c in report["per_column"]}
    assert by_column["a"]["missing"] == 1
    assert by_column["a"]["missing_pct"] == pytest.approx(33.33, abs=0.01)
    assert by_column["c"]["missing_pct"] == 0.0
    assert [c["column"] for c in report["columns_with_missing"]] == ["a", "b"]


def test_complete_data_reports_full_completeness():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    report = completeness_report(df)
    assert report["complete_rows"] == 2 and report["complete_rows_pct"] == 100.0
    assert report["columns_with_missing"] == []