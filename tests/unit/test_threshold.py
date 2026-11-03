import math

from churnlens.evaluation.threshold import campaign_outcome, sweep_thresholds

Y = [1, 1, 0, 0]
P = [0.9, 0.6, 0.7, 0.1]
CHARGES = [100, 50, 80, 60]
SETTINGS = dict(offer_cost=10, success_rate=0.5, horizon_months=12, margin=1.0)


def test_campaign_numbers_match_hand_calculation():
    out = campaign_outcome(Y, P, CHARGES, threshold=0.5, **SETTINGS)
    assert out["targeted"] == 3            # 0.9, 0.6, 0.7
    assert out["churners_reached"] == 2    # customers 1 and 2
    assert out["campaign_cost"] == 30
    assert out["estimated_retained"] == 1.0
    assert out["revenue_preserved"] == 900  # (100 + 50) * 12 * 0.5
    assert out["net_benefit"] == 870
    assert out["roi"] == 29


def test_threshold_above_all_scores_targets_nobody():
    out = campaign_outcome(Y, P, CHARGES, threshold=0.99, **SETTINGS)
    assert out["targeted"] == 0
    assert out["net_benefit"] == 0
    assert math.isnan(out["roi"])


def test_sweep_returns_one_row_per_threshold():
    table = sweep_thresholds(Y, P, CHARGES, [0.2, 0.5, 0.8], **SETTINGS)
    assert len(table) == 3