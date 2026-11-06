import pytest

from backend.app.services.customer_profile import (
    SMALL_BAND, build_notes, probability_band, risk_category_definition,
)


def notes(**overrides):
    args = dict(prediction_source="holdout_test", tenure=12, probability=0.5,
                band_labeled=0, band_churned=0)
    args.update(overrides)
    return build_notes(**args)


def test_probability_band_edges():
    assert probability_band(0.0) == (0.0, 0.2)
    assert probability_band(0.1999) == (0.0, 0.2)
    assert probability_band(0.2) == (0.2, 0.4)
    assert probability_band(0.6) == (0.6, 0.8)
    assert probability_band(1.0) == (0.8, 1.0)


@pytest.mark.parametrize("source, fragment", [
    ("out_of_fold_train", "cross-validated"),
    ("holdout_test", "held out"),
    ("new_data", "after the model was trained"),
])
def test_source_note_explains_where_the_probability_comes_from(source, fragment):
    result = notes(prediction_source=source)
    assert len(result) == 1
    assert result[0]["level"] == "info"
    assert fragment in result[0]["text"]


def test_zero_tenure_gets_a_warning():
    assert any(n["level"] == "warning" and "0 months" in n["text"] for n in notes(tenure=0))
    assert not any("0 months" in n["text"] for n in notes(tenure=5))


def test_band_evidence_and_small_band_warning():
    result = notes(probability=0.85, band_labeled=3, band_churned=2)
    assert any("(80% to 100%)" in n["text"] and "67%" in n["text"] for n in result)
    assert any(n["level"] == "warning" and n["text"].startswith("Only 3") for n in result)


def test_large_band_has_no_noise_warning():
    result = notes(probability=0.3, band_labeled=SMALL_BAND, band_churned=30)
    assert any("30% actually churned" in n["text"] for n in result)
    assert not any(n["level"] == "warning" for n in result)


def test_no_known_outcomes_means_no_band_note():
    assert not any("predicted-risk band" in n["text"] for n in notes())


def test_risk_definition_text():
    assert risk_category_definition(0.2) == (
        "Low below 0.20, Medium 0.20 to 0.50, High 0.50 and above (display cutoffs, not statistics)"
    )
    assert "not recorded" in risk_category_definition(None)