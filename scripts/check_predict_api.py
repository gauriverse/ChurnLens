import json
import urllib.error
import urllib.request

import pandas as pd

from churnlens.features.schema import FEATURES

URL = "http://127.0.0.1:8000/api/v1/predict"
test = pd.read_csv("data/processed/test.csv")
train = pd.read_csv("data/processed/train.csv")
stored = pd.read_csv("data/processed/predictions_v1.csv").set_index("customerID")


def post(body):
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")

        try:
            result = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            result = {"detail": raw or str(error.reason)}

        return error.code, result
    except urllib.error.URLError:
        raise SystemExit("Could not reach the API. Is uvicorn running on port 8000?")


mismatches = 0
print("Held-out customers: the API must reproduce the stored probability (same model file).")
for _, row in test.head(10).iterrows():
    status, result = post(json.loads(row[FEATURES].to_json()))
    if status != 200:
        raise SystemExit(f"{row['customerID']}: API returned {status}: {result}")
    want = float(stored.loc[row["customerID"], "churn_probability"])
    ok = abs(result["churn_probability"] - want) < 0.0001
    mismatches += 0 if ok else 1
    warnings = sum(n["level"] == "warning" for n in result["notes"])
    print(f"  {row['customerID']}  api={result['churn_probability']:.4f}  stored={want:.4f}  "
          f"{result['risk_category']:<6} warnings={warnings}  {'OK' if ok else 'MISMATCH'}")

body = json.loads(test.iloc[0][FEATURES].to_json())
body["Contract"] = "Weekly"
status, result = post(body)
print(f"\nUnknown Contract value -> HTTP {status}: {result.get('detail')}")

row = train.iloc[0]
status, result = post(json.loads(row[FEATURES].to_json()))
print(f"\nTraining customer {row['customerID']}: api={result['churn_probability']:.4f}  "
      f"stored out-of-fold={float(stored.loc[row['customerID'], 'churn_probability']):.4f}")
print("  (close but not identical on purpose: the stored value comes from a cross-validation "
      "model that never saw this customer, while the API uses the final model)")

print("\nall held-out probabilities match" if not mismatches else f"\n{mismatches} mismatches")
raise SystemExit(1 if mismatches else 0)