import json
import sys
import time
import urllib.error
import urllib.request

import pandas as pd

from churnlens.features.schema import FEATURES

if len(sys.argv) != 2:
    raise SystemExit("usage: python scripts/check_live.py https://your-service.onrender.com")
BASE = sys.argv[1].rstrip("/")


def parse(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None  # for example an HTML "service is starting" page


def call(method, path, body=None):
    """Send one request. Returns (status, parsed JSON or None, seconds)."""
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        return None, str(error), time.perf_counter() - start
    return status, parse(raw), time.perf_counter() - start


print(f"Checking {BASE}")
print("Waking the service. A free Render service sleeps when idle, so this can take a minute...")
for attempt in range(1, 13):
    status, payload, seconds = call("GET", "/health")
    if status == 200 and payload == {"status": "ok"}:
        print(f"  awake after {seconds:.0f} s (try {attempt})\n")
        break
    print(f"  try {attempt}: not ready yet (status {status}), waiting 10 s")
    time.sleep(10)
else:
    raise SystemExit("The service did not wake up in about 2 minutes. Open the Logs tab in Render.")

failures = []


def get(path):
    status, payload, seconds = call("GET", path)
    if status != 200:
        raise AssertionError(f"HTTP {status}: {payload}")
    return payload, seconds


def post(path, body):
    status, payload, seconds = call("POST", path, body)
    if status != 200:
        raise AssertionError(f"HTTP {status}: {payload}")
    return payload, seconds


def run(name, check):
    try:
        ok, detail = check()
    except Exception as error:  # a missing field or a non-200 answer means something is wrong
        ok, detail = False, f"{type(error).__name__}: {error}"
    print(f"{'OK    ' if ok else 'FAILED'}  {name:<38} {detail}")
    if not ok:
        failures.append(name)


def database():
    payload, s = get("/health/db")
    return payload == {"status": "ok", "database": "connected"}, f"({s:.1f} s)"


def insights():
    payload, s = get("/api/v1/insights")
    k = {item["key"]: item["value"] for item in payload["kpis"]}
    ok = k["total_customers"] == 7043 and abs(k["churn_rate"] - 0.2654) < 0.0005
    return ok, f"customers={k['total_customers']}, churn rate={k['churn_rate']} ({s:.1f} s)"


def customers():
    payload, s = get("/api/v1/customers?page_size=3")
    ok = payload["total"] == 7043 and len(payload["items"]) == 3
    return ok, f"total={payload['total']}, top customer={payload['items'][0]['customer_id']} ({s:.1f} s)"


def one_customer():
    payload, s = get("/api/v1/customers/7590-VHVEG")
    probability = payload["prediction"]["churn_probability"]
    ok = payload["customer_id"] == "7590-VHVEG" and 0 <= probability <= 1
    return ok, f"probability={probability} ({s:.1f} s)"


def segments():
    payload, s = get("/api/v1/segments")
    return len(payload["segments"]) == 5, f"{len(payload['segments'])} segments ({s:.1f} s)"


def metrics():
    payload, s = get("/api/v1/model/metrics")
    auc = payload["held_out_test"]["roc_auc"]
    return auc == 0.842, f"held-out ROC-AUC={auc} ({s:.1f} s)"


def model_health():
    payload, s = get("/api/v1/model/health")
    ok = payload["schema_compatibility"]["compatible"] and payload["performance"]["status"] == "not_verified"
    return ok, f"schema compatible, performance not verified ({s:.1f} s)"


def history():
    payload, s = get("/api/v1/analysis/history")
    return payload["total"] >= 1, f"{payload['total']} run(s) ({s:.1f} s)"


def simulate():
    body = {"scenarios": [{"name": "Baseline", "offer_cost": 40, "success_rate": 0.3, "risk_threshold": 0.2}]}
    payload, s = post("/api/v1/simulate", body)
    result = payload["scenarios"][0]
    ok = result["customers_targeted"] == 3423 and abs(result["expected_net_benefit"] - 314206.38) < 0.02
    return ok, f"targeted={result['customers_targeted']}, net benefit={result['expected_net_benefit']} ({s:.1f} s)"


def predict():
    row = pd.read_csv("data/processed/test.csv").iloc[0]
    stored = pd.read_csv("data/processed/predictions_v1.csv").set_index("customerID")
    expected = float(stored.loc[row["customerID"], "churn_probability"])
    payload, s = post("/api/v1/predict", json.loads(row[FEATURES].to_json()))
    got = payload["churn_probability"]
    return abs(got - expected) < 0.0001, f"api={got:.4f}, expected={expected:.4f} ({s:.1f} s, includes loading the model)"


CHECKS = [
    ("database connection (/health/db)", database),
    ("overview KPIs (/insights)", insights),
    ("risk-ranked customer table", customers),
    ("one customer profile", one_customer),
    ("segments", segments),
    ("model metrics", metrics),
    ("model health", model_health),
    ("analysis history", history),
    ("retention simulator (POST)", simulate),
    ("prediction (POST)", predict),
]
for name, check in CHECKS:
    run(name, check)

print()
if failures:
    print(f"{len(failures)} of {len(CHECKS)} checks failed: {failures}")
else:
    print("All checks passed. The live service matches your local results.")
raise SystemExit(1 if failures else 0)