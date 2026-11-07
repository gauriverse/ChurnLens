import json
import urllib.error
import urllib.request

import pandas as pd

URL = "http://127.0.0.1:8000/api/v1/simulate"
expected = pd.read_csv("data/processed/scenario_comparison_v1.csv")

scenarios = [
    {
        "name": r.scenario,
        "offer_cost": float(r.offer_cost),
        "success_rate": float(r.success_rate),
        "risk_threshold": float(r.risk_threshold),
        "max_customers": None if pd.isna(r.max_customers) else int(r.max_customers),
    }
    for r in expected.itertuples(index=False)
]

request = urllib.request.Request(
    URL,
    data=json.dumps({"scenarios": scenarios}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request) as response:
        body = json.load(response)
except urllib.error.HTTPError as error:
    raise SystemExit(f"API returned {error.code}: {error.read().decode()}")
except urllib.error.URLError:
    raise SystemExit("Could not reach the API. Is uvicorn running on port 8000?")

print("analysis_run", body["analysis_run_id"], "| customers considered", body["customers_considered"])
mismatches = 0
for want, got in zip(expected.itertuples(index=False), body["scenarios"]):
    pairs = {
        "customers_targeted": (int(want.customers_targeted), got["customers_targeted"]),
        "campaign_cost": (float(want.campaign_cost), got["campaign_cost"]),
        "expected_net_benefit": (float(want.expected_net_benefit), got["expected_net_benefit"]),
        "expected_roi": (float(want.expected_roi), got["expected_roi"]),
    }
    bad = [k for k, (a, b) in pairs.items() if b is None or abs(a - b) > 0.011]
    mismatches += len(bad)
    status = "OK" if not bad else f"MISMATCH {bad}"
    print(f"{want.scenario:30} {status:10} targeted={got['customers_targeted']} "
          f"net={got['expected_net_benefit']} roi={got['expected_roi']}")
    for w in got["warnings"]:
        print("    warning:", w)

print("all scenarios match the Milestone 8 results" if not mismatches else f"{mismatches} mismatches")