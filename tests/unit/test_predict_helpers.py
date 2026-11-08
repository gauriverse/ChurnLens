from backend.app.services.predict import ADD_ON_SERVICES, category_problems, input_warnings

RANGES = {
    "tenure": (0.0, 72.0),
    "MonthlyCharges": (18.25, 118.75),
    "TotalCharges": (0.0, 8684.8),
}


def customer(**overrides):
    row = {
        "tenure": 12, "MonthlyCharges": 50.0, "TotalCharges": 600.0, "SeniorCitizen": 0,
        "gender": "Female", "Partner": "Yes", "Dependents": "No", "PhoneService": "Yes",
        "MultipleLines": "No", "InternetService": "DSL", "OnlineSecurity": "Yes",
        "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "Yes",
        "StreamingTV": "No", "StreamingMovies": "No", "Contract": "Month-to-month",
        "PaperlessBilling": "Yes", "PaymentMethod": "Mailed check",
    }
    row.update(overrides)
    return row


def texts(notes):
    return [n["text"] for n in notes]


def test_a_consistent_row_inside_the_reference_range_has_no_warnings():
    assert input_warnings(customer(), RANGES) == []


def test_values_outside_the_reference_range_are_flagged():
    found = texts(input_warnings(customer(tenure=90, MonthlyCharges=150.0), RANGES))
    assert len(found) == 2
    assert found[0].startswith(
        "tenure 90 is outside the range seen in the reference data (0 to 72)"
    )
    assert found[1].startswith(
        "MonthlyCharges 150 is outside the range seen in the reference data (18.25 to 118.75)"
    )


def test_range_boundaries_are_inclusive_and_missing_ranges_are_ignored():
    assert input_warnings(customer(tenure=72, MonthlyCharges=18.25), RANGES) == []
    assert input_warnings(customer(tenure=900), None) == []
    assert input_warnings(customer(tenure=900), {}) == []


def test_internet_and_add_on_conflicts_are_flagged():
    everything = texts(input_warnings(customer(InternetService="No")))
    assert len(everything) == 1
    assert "OnlineSecurity" in everything[0] and "are inconsistent" in everything[0]

    consistent = {name: "No internet service" for name in ADD_ON_SERVICES}
    assert input_warnings(customer(InternetService="No", **consistent)) == []

    one = texts(input_warnings(customer(OnlineSecurity="No internet service")))
    assert len(one) == 1 and "OnlineSecurity is inconsistent" in one[0]


def test_phone_conflicts_are_flagged():
    assert input_warnings(customer(PhoneService="No", MultipleLines="No phone service")) == []
    wrong = texts(input_warnings(customer(PhoneService="No", MultipleLines="Yes")))
    assert len(wrong) == 1 and "No phone service" in wrong[0]
    other_way = input_warnings(customer(PhoneService="Yes", MultipleLines="No phone service"))
    assert len(other_way) == 1


def test_zero_tenure_is_flagged():
    found = texts(input_warnings(customer(tenure=0, TotalCharges=0.0)))
    assert len(found) == 1 and "0 months of tenure" in found[0]


def test_unknown_category_values_are_reported():
    categories = {
        "Contract": ["Month-to-month", "One year", "Two year"],
        "gender": ["Female", "Male"],
    }
    assert category_problems(customer(), categories) == []
    problems = category_problems(customer(Contract="Weekly", gender="Other"), categories)
    assert len(problems) == 2
    assert problems[0] == (
        "Contract: 'Weekly' is not a value the model was trained on "
        "(allowed: Month-to-month, One year, Two year)"
    )
    assert problems[1].startswith("gender: 'Other'")