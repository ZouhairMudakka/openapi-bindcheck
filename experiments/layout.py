"""Shared repository/cache/result paths for the reproduction scripts."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get("BINDCHECK_CACHE", ROOT / ".cache")).resolve()
RESULTS = Path(os.environ.get("BINDCHECK_RESULTS", ROOT / "results" / "local")).resolve()
ADK_PIN = "044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5"
FASTMCP_PIN = "92e44ffcc04b29f960a6c678f44fac226ccc0ea6"
OPENWEBUI_PIN = "8bd8b4fac5e059578ac0c74b3c18d11139f88b7d"


def result_path(name: str | Path) -> Path:
    """Resolve an output name under RESULTS and create its parent directory."""
    path = RESULTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
