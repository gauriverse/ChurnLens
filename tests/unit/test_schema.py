from churnlens.features.schema import (
    CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, check_schema, dtype_kind,
)


def telco_like():
    columns = {"tenure": "int64", "SeniorCitizen": "int64",
               "MonthlyCharges": "float64", "TotalCharges": "float64"}
    columns.update({name: "object" for name in CATEGORICAL_FEATURES})
    columns.update({"customerID": "object", "Churn": "int64"})
    return columns


def test_feature_lists_are_consistent():
    assert FEATURES == NUMERIC_FEATURES + CATEGORICAL_FEATURES
    assert len(FEATURES) == 19 and len(set(FEATURES)) == 19


def test_telco_like_schema_is_compatible():
    report = check_schema(telco_like())
    assert report["compatible"] is True
    assert report["missing_columns"] == [] and report["type_mismatches"] == []
    assert report["extra_columns"] == []
    assert report["id_column_present"] and report["target_column_present"]
    assert report["required_columns"] == 19


def test_missing_column_is_reported():
    columns = telco_like()
    del columns["Contract"]
    report = check_schema(columns)
    assert report["compatible"] is False
    assert report["missing_columns"] == ["Contract"]


def test_type_mismatches_are_reported():
    columns = telco_like()
    columns["TotalCharges"] = "object"     # blank strings were never converted to numbers
    columns["Contract"] = "float64"
    report = check_schema(columns)
    assert report["compatible"] is False
    assert report["type_mismatches"] == [
        {"column": "TotalCharges", "expected": "numeric", "found": "object"},
        {"column": "Contract", "expected": "text", "found": "float64"},
    ]


def test_newer_pandas_text_dtype_names_are_accepted():
    for name in ["str", "string", "string[python]", "category", "object"]:
        assert dtype_kind(name) == "text"
    for name in ["int64", "Int64", "uint8", "float32", "float64"]:
        assert dtype_kind(name) == "numeric"
    assert dtype_kind("bool") == "other"
    columns = telco_like()
    columns["Contract"] = "str"
    assert check_schema(columns)["compatible"] is True


def test_extra_columns_are_listed_but_id_and_target_are_not():
    columns = telco_like()
    columns["Notes"] = "object"
    assert check_schema(columns)["extra_columns"] == ["Notes"]