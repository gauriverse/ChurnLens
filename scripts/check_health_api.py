import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def get(path):
    try:
        with urllib.request.urlopen(BASE + path) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{path} returned {error.code}: {error.read().decode()[:300]}")
    except urllib.error.URLError:
        raise SystemExit("Could not reach the API. Is uvicorn running on port 8000?")


failures = []


def check(name, ok, detail=""):
    print(f"{'OK      ' if ok else 'MISMATCH'}  {name}  {detail}")
    if not ok:
        failures.append(name)


health = get("/model/health")
history = get("/analysis/history")

# ---- prediction distribution, against the SQL calibration table ----
dist = health["prediction_distribution"]
counts = [b["customers"] for b in dist["bins"]]
pairs = [counts[i] + counts[i + 1] for i in range(0, 10, 2)]
check("five 0.2-wide bands match SQL 03", pairs == [3620, 1302, 1131, 952, 38], str(pairs))
check("total predictions", dist["total"] == 7043, str(dist["total"]))
check("mean predicted is about 0.266", abs(dist["mean_predicted"] - 0.266) < 0.003, str(dist["mean_predicted"]))
check("observed churn rate is 0.2654", abs(dist["observed_churn_rate"] - 0.2654) < 0.0005, str(dist["observed_churn_rate"]))
risk = {c["category"]: c["customers"] for c in dist["by_risk_category"]}
check("Low risk equals the lowest band", risk.get("Low") == 3620, str(risk))
check("Medium + High equals the Baseline scenario's 3,423", risk.get("Medium", 0) + risk.get("High", 0) == 3423, str(risk))
sources = {s["source"]: s["customers"] for s in dist["by_source"]}
check("5,634 out-of-fold and 1,409 held-out", sources == {"out_of_fold_train": 5634, "holdout_test": 1409}, str(sources))

# ---- live database checks ----
completeness = health["database_completeness"]
check(
    "no missing values in the database after cleaning",
    completeness["customers"] == 7043 and all(c["missing"] == 0 for c in completeness["columns"]),
    str(completeness["customers"]),
)
schema = health["schema_compatibility"]
check("schema is compatible with the model", bool(schema and schema["compatible"]),
      "" if schema is None else schema["explanation"])

# ---- stored monitoring results ----
quality = health["data_quality"]
if not quality["available"]:
    check("data quality results are stored", False, "run: python -m scripts.compute_monitoring")
else:
    missing = {c["column"]: c["missing"] for c in quality["columns_with_missing"]}
    check(
        "raw file: 7,043 rows, 21 columns, 7,032 complete, 11 blank TotalCharges",
        (quality["rows"], quality["columns"], quality["complete_rows"]) == (7043, 21, 7032)
        and missing == {"TotalCharges": 11},
        f"{quality['rows']} rows, {quality['complete_rows']} complete, missing={missing}",
    )

drift = health["drift"]
if not drift["available"]:
    check("drift results are stored", False, "run: python -m scripts.compute_monitoring")
else:
    measured = {f["feature"]: f["psi"] for f in drift["measured"]["features"]}
    worst = max(measured.values())
    check("measured drift is small for every feature", worst < 0.10, f"largest PSI {worst}")
    check("measured prediction PSI is small", drift["measured"]["predictions"]["psi"] < 0.10,
          str(drift["measured"]["predictions"]["psi"]))
    for sim in drift["simulated"]:
        psi = {f["feature"]: f["psi"] for f in sim["features"]}
        changed = sim["changed_columns"]
        check(f"simulated '{sim['key']}' is labelled simulated",
              sim["kind"] == "simulated" and sim["note"].startswith("Simulated"))
        check(f"simulated '{sim['key']}': untouched features equal the baseline",
              all(psi[name] == measured[name] for name in psi if name not in changed))
        check(f"simulated '{sim['key']}': altered features show a shift",
              max(psi[name] for name in changed) >= 0.10,
              f"largest altered PSI {max(psi[name] for name in changed)}")

perf = health["performance"]
check("performance is reported as not verified",
      perf["status"] == "not_verified" and perf["labeled_new_data_customers"] == 0)

latest = history["runs"][0]
check("latest run: 7,043 predictions, 5 segments, 3,541 recommendations",
      (latest["predictions"], latest["segments"], latest["recommendations"]) == (7043, 5, 3541),
      str((latest["predictions"], latest["segments"], latest["recommendations"])))
check("latest run has survival curves and monitoring results",
      latest["has_survival_curves"] and latest["has_monitoring_results"])

print("\nFor information:")
print("  runs stored:", history["total"])
if drift["available"]:
    print("  largest measured PSI:", sorted(measured.items(), key=lambda kv: -kv[1])[:3])
    for sim in drift["simulated"]:
        e = sim["prediction_effect"]
        print(f"  {sim['key']}: mean predicted {e['mean_predicted_before']} -> {e['mean_predicted_after']}, "
              f"share above threshold {e['share_flagged_before']} -> {e['share_flagged_after']}")

print()
print("all checks passed" if not failures else f"{len(failures)} mismatches: {failures}")
raise SystemExit(1 if failures else 0)