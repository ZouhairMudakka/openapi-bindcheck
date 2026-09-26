"""Verify installed Python source against the immutable upstream package trees."""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform

from layout import CACHE, RESULTS

# Tree digest: SHA256 of the ASCII, sorted-key, compact JSON mapping from
# package-relative POSIX .py filename to the SHA256 of its unmodified bytes.
PROJECTS = {
    "adk": {
        "pin": "044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5",
        "module": "google.adk",
        "distribution": "google-adk",
        "vendor": "adk-python-044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5",
        "package": "src/google/adk",
        "count": 765,
        "tree_sha256": "49a18d87db8328a2babebaedeadad22be47badc1fc0d3db12081b9e54a0b2c1b",
    },
    "fastmcp": {
        "pin": "92e44ffcc04b29f960a6c678f44fac226ccc0ea6",
        "module": "fastmcp",
        "distribution": "fastmcp-slim",
        "vendor": "fastmcp-92e44ffcc04b29f960a6c678f44fac226ccc0ea6",
        "package": "fastmcp_slim/fastmcp",
        "count": 258,
        "tree_sha256": "d82baa24c7a9364756205de4e9a3a1c6e32f05336fed9adabba3b867df2619be",
    },
}


def file_hashes(package: Path) -> dict[str, str]:
    return {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(package.rglob("*.py"))
    }


def verify_project(adapter: str) -> dict:
    """Fail on missing/extra/changed .py files; report no local filesystem paths."""
    project = PROJECTS[adapter]
    os.environ["FASTMCP_CHECK_FOR_UPDATES"] = "off"
    source = CACHE / "vendor" / project["vendor"] / project["package"]
    source_hashes = file_hashes(source)
    canonical = json.dumps(source_hashes, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    tree_digest = hashlib.sha256(canonical).hexdigest()
    if len(source_hashes) != project["count"] or tree_digest != project["tree_sha256"]:
        raise RuntimeError(f"{adapter}: vendor Python source does not match the pinned package tree")
    module = importlib.import_module(project["module"])
    installed_hashes = file_hashes(Path(module.__file__).resolve().parent)
    if installed_hashes != source_hashes:
        missing = sorted(set(source_hashes) - set(installed_hashes))
        extra = sorted(set(installed_hashes) - set(source_hashes))
        changed = sorted(name for name in set(source_hashes) & set(installed_hashes) if source_hashes[name] != installed_hashes[name])
        raise RuntimeError(f"{adapter}: installed source mismatch: missing={missing}, extra={extra}, changed={changed}")
    return {
        "pin": project["pin"],
        "package": project["module"],
        "distribution_version": importlib.metadata.version(project["distribution"]),
        "verified_python_file_count": len(source_hashes),
        "tree_sha256": tree_digest,
        "files": source_hashes,
    }


def main() -> None:
    result = {
        "python": platform.python_version(),
        "packages": {adapter: verify_project(adapter) for adapter in PROJECTS},
        "dependencies": dict(sorted((dist.metadata["Name"], dist.version) for dist in importlib.metadata.distributions())),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "provenance.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({adapter: data["verified_python_file_count"] for adapter, data in result["packages"].items()}))


if __name__ == "__main__":
    main()
