import pandas as pd

from churnlens.models.train import pick_threshold


def test_pick_threshold_prefers_stable_plateau_over_lone_spike():
    sweep = pd.DataFrame({
        "threshold": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "net_benefit": [0, 120, 0, 90, 95, 92, 0],
    })
    # The raw maximum is at 0.2 (a lone spike); the smoothed maximum is the plateau at 0.5.
    assert pick_threshold(sweep) == 0.5