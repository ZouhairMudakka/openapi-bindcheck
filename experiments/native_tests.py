"""Run exact, unchanged selected upstream suites, optionally with diagnostic repairs.

This is not either project's full suite. Ancestor conftest files are excluded;
only pytest-asyncio and a minimal local configuration are loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from tempfile import TemporaryDirectory
from pathlib import Path

from layout import CACHE, RESULTS
from provenance import PROJECTS, verify_project

SUITES = {
    "adk": {
        "directory": "tests/unittests/tools/openapi_tool/openapi_spec_parser",
        "expected_count": 131,
        "files": {
            "test_operation_parser.py": "202009ae48da827b35d8f76326ad6de5f67cadc4c7cfff70f9b7795677ebb859",
            "test_rest_api_tool.py": "18f62063b4f6183fb5a3e169a9da08274d1ecbb626df813fd62c53018561c966",
        },
    },
    "fastmcp": {
        "directory": "tests/server/providers/openapi",
        "expected_count": 25,
        "files": {
            "test_whole_body_parameter_collisions.py": "781cdcd02c1dff50ae082d595db6d6d62168d535c751eb44a74231248fe37b96",
        },
    },
}


class Counts:
    def __init__(self):
        self.collected = 0
        self.counts = {}

    def pytest_sessionfinish(self, session, exitstatus):
        self.collected = session.testscollected
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        self.counts = {name: len(reporter.stats.get(name, [])) for name in ("passed", "failed", "error", "skipped", "xfailed", "xpassed", "deselected", "warnings")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=tuple(SUITES), required=True)
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    suite = SUITES[args.adapter]
    project = PROJECTS[args.adapter]
    source = CACHE / "vendor" / project["vendor"]
    testdir = source / suite["directory"]
    tests = [testdir / name for name in suite["files"]]
    for path, expected in zip(tests, suite["files"].values()):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Refusing modified upstream test file: {path.name}")
    provenance = verify_project(args.adapter)
    if args.repair:
        if args.adapter == "adk":
            from adk_repairs import install
            install("both")
        else:
            from fastmcp_repairs import install
            install()

    # Ignore user-level plugin and option configuration that could change the
    # selected tests; retain pytest's built-in plugins and explicit asyncio.
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ.pop("PYTEST_ADDOPTS", None)
    os.environ.pop("PYTEST_PLUGINS", None)
    import pytest
    counts = Counts()
    with TemporaryDirectory(prefix="bindcheck-pytest-") as temporary:
        config = Path(temporary) / "pytest.ini"
        config.write_text("[pytest]\nasyncio_mode = auto\n", encoding="utf-8")
        status = int(pytest.main([
            "-q", "--tb=short", "-p", "no:cacheprovider", "-p", "pytest_asyncio.plugin",
            "-c", str(config), "--rootdir", str(source), "--confcutdir", str(testdir),
            *map(str, tests),
        ], plugins=[counts]))
    complete = counts.collected == suite["expected_count"] and counts.counts.get("passed") == suite["expected_count"]
    success = status == 0 and complete
    result = {
        "adapter": args.adapter,
        "mode": "corrected" if args.repair else "original",
        "source_pin": project["pin"],
        "python": platform.python_version(),
        "scope": "selected unchanged native test modules; ancestor conftest excluded",
        "configuration": {"asyncio_mode": "auto", "plugins": ["pytest_asyncio.plugin"], "automatic_plugin_loading": False},
        "test_files": {f"{suite['directory']}/{name}": digest for name, digest in suite["files"].items()},
        "package_tree_sha256": provenance["tree_sha256"],
        "verified_python_file_count": provenance["verified_python_file_count"],
        "expected_count": suite["expected_count"],
        "collected": counts.collected,
        "counts": counts.counts,
        "pytest_exit_code": status,
        "success": success,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    filename = f"native-{args.adapter}-{result['mode']}.json"
    (RESULTS / filename).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if success else status or 1


if __name__ == "__main__":
    raise SystemExit(main())
