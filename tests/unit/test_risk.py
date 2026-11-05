import pytest

from churnlens.evaluation.risk import risk_category

def test_category_boundaries():
    assert risk_category(0.5, 0.2) == "High"
    assert risk_category(0.499, 0.2) == "Medium"
    assert risk_category(0.2, 0.2) == "Medium"
    assert risk_category(0.199, 0.2) == "Low"

def test_invalid_cutoffs_are_rejected():
    with pytest.raises(ValueError):
        risk_category(0.3,0.6)