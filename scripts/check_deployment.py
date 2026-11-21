import re
import sys
import time
import urllib.error
import urllib.request

if len(sys.argv) != 3:
    raise SystemExit(
        "usage: python scripts/check_deployment.py https://your-app.vercel.app https://your-api.onrender.com"
    )
FRONTEND, API = (arg.rstrip("/") for arg in sys.argv[1:3])


def lower(headers):
    return {key.lower(): value for key, value in headers.items()}


def request(url, method="GET", headers=None):
    """Returns (status or None, lower-cased response headers, body text)."""
    req = urllib.request.Request(
        url, method=method, headers={"User-Agent": "churnlens-deployment-check", **(headers or {})}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, lower(response.headers), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, lower(error.headers), error.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as error:
        return None, {}, str(error)


print(f"Waking the API at {API} (a free Render service sleeps when idle)...")
for attempt in range(1, 13):
    status, _, _ = request(API + "/health")
    if status == 200:
        print(f"  awake (try {attempt})\n")
        break
    print(f"  try {attempt}: status {status}, waiting 10 s")
    time.sleep(10)
else:
    raise SystemExit("The API did not wake up in about 2 minutes. Open the Logs tab in Render.")

failures = []


def check(name, ok, detail=""):
    print(f"{'OK    ' if ok else 'FAILED'}  {name:<58} {detail}")
    if not ok:
        failures.append(name)


# 1. every address serves the app (this needs the rewrite in vercel.json)
for path in ["/", "/customers", "/customers/7590-VHVEG", "/some/unknown/address"]:
    status, _, body = request(FRONTEND + path)
    check(f"frontend serves the app at {path}", status == 200 and 'id="root"' in body, f"HTTP {status}")

# 2. the build knows where the API is (VITE_API_URL must be set BEFORE Vercel builds)
_, _, html = request(FRONTEND + "/")
match = re.search(r'src="(/assets/[^"]+\.js)"', html)
if match:
    _, _, script = request(FRONTEND + match.group(1))
    found = API in script
    check("the built app contains the API address", found,
          "" if found else "VITE_API_URL was missing when Vercel built the app")
else:
    check("the built app contains the API address", False, "could not find the script in index.html")

# 3. the API accepts the frontend and nobody else
_, headers, _ = request(API + "/health", headers={"Origin": FRONTEND})
allowed = headers.get("access-control-allow-origin")
check("API allows the frontend's address", allowed == FRONTEND, f"got {allowed!r}")

_, headers, _ = request(API + "/health", headers={"Origin": "https://evil.example"})
check("API does not allow other addresses", "access-control-allow-origin" not in headers)

status, headers, _ = request(
    API + "/api/v1/simulate",
    method="OPTIONS",
    headers={
        "Origin": FRONTEND,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
)
check("browser preflight for the simulator's POST is accepted",
      status == 200 and headers.get("access-control-allow-origin") == FRONTEND, f"HTTP {status}")

print()
print("All checks passed." if not failures else f"{len(failures)} checks failed: {failures}")
raise SystemExit(1 if failures else 0)