import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_importing_the_api_does_not_load_heavy_ml_libraries():
    code = (
        "import sys; import backend.app.main; "
        "heavy = [m for m in ('lifelines', 'shap', 'xgboost', 'sklearn') if m in sys.modules]; "
        "print(','.join(heavy))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, check=True
    )
    assert result.stdout.strip() == "", result.stdout

def test_schema_and_drift_modules_do_not_load_heavy_ml_libraries():
    code = (
        "import sys; import churnlens.features.schema, churnlens.monitoring.drift; "
        "heavy = [m for m in ('lifelines', 'shap', 'xgboost', 'sklearn') if m in sys.modules]; "
        "print(','.join(heavy))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, check=True
    )
    assert result.stdout.strip() == "", result.stdout