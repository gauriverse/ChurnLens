import re

RUNTIME = [
    "fastapi", "uvicorn", "sqlalchemy", "psycopg", "psycopg-binary", "pydantic",
    "python-dotenv", "pandas", "numpy", "scipy", "scikit-learn", "joblib",
]


def normal(name):
    return re.sub(r"[-_.]+", "-", name).lower()


# Windows PowerShell's ">" writes UTF-16, so detect the encoding instead of assuming
raw = open("requirements.txt", "rb").read()
text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")

pinned = {}
for line in text.splitlines():
    line = line.strip()
    if "==" in line and not line.startswith("#"):
        pinned[normal(line.split("==", 1)[0])] = line

lines, missing = [], []
for name in RUNTIME:
    if normal(name) in pinned:
        lines.append(pinned[normal(name)])
    else:
        missing.append(name)

if missing:
    raise SystemExit(f"not found in requirements.txt: {missing}. Run pip freeze first.")

with open("requirements-api.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))