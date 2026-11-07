from churnlens.segmentation.summary import (
    HIGH_PRIORITY_SHARE, MEDIUM_PRIORITY_SHARE, characteristics, priority_tier,
)

ROW = dict(pct_fiber=1.0, pct_dsl=0.0, avg_tenure=17.36, avg_addons=1.65,
           avg_contract_months=1.33, share_of_churned_revenue=0.666)


def test_characteristics_are_rounded_plain_numbers():
    assert characteristics(ROW) == {
        "avg_tenure_months": 17.4,
        "avg_add_on_services": 1.65,
        "avg_contract_months": 1.3,
        "share_fiber": 1.0,
        "share_dsl": 0.0,
        "share_no_internet": 0.0,
        "share_of_churned_revenue_historical": 0.666,
    }


def test_share_without_internet_is_the_remainder():
    assert characteristics({**ROW, "pct_fiber": 0.0, "pct_dsl": 0.0})["share_no_internet"] == 1.0
    assert characteristics({**ROW, "pct_fiber": 0.52, "pct_dsl": 0.48})["share_no_internet"] == 0.0


def test_priority_cutoffs_are_the_documented_constants():
    assert (HIGH_PRIORITY_SHARE, MEDIUM_PRIORITY_SHARE) == (0.30, 0.10)
    assert priority_tier(0.30) == "High"
    assert priority_tier(0.299) == "Medium"
    assert priority_tier(0.10) == "Medium"
    assert priority_tier(0.099) == "Low"