"""Fetch hash-locked public sources and install the bounded reproduction environment.

Run in a disposable Python 3.12 venv. Network is used only by setup, not probes.
No credentials are read. Downloaded upstream projects retain their own licenses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile

from layout import ROOT, CACHE


def fetch(url, target, digest):
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Hash mismatch in existing {target.name}")
        return
    with urlopen(Request(url, headers={"User-Agent": "openapi-bindcheck-reproduction"}), timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError(f"Downloaded content hash changed: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def extract(archive, vendor, directory):
    # Reject traversal/absolute paths; omit upstream symlinks rather than follow
    # them. The pinned FastMCP archive contains unused maintainer-doc links.
    with zipfile.ZipFile(archive) as source:
        regular = []
        for item in source.infolist():
            path = PurePosixPath(item.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in item.filename
                    or ":" in item.filename or not path.parts or path.parts[0] != directory):
                raise RuntimeError(f"Unsafe archive member: {item.filename}")
            if ((item.external_attr >> 16) & 0o170000) != 0o120000:
                regular.append(item)
        source.extractall(vendor, members=regular)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-only", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "experiments/sources.json").read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    for entry in manifest["archives"]:
        target = CACHE / "vendor" / entry["directory"]
        marker = target / ".bindcheck-archive-sha256"
        if target.exists():
            if not marker.exists() or marker.read_text().strip() != entry["sha256"]:
                raise RuntimeError(f"Unverified pre-existing source tree: {target}; use a fresh BINDCHECK_CACHE")
        else:
            with tempfile.TemporaryDirectory(prefix="bindcheck-", dir=CACHE) as temp:
                archive = Path(temp) / "source.zip"
                fetch(entry["url"], archive, entry["sha256"])
                extract(archive, CACHE / "vendor", entry["directory"])
            marker.write_text(entry["sha256"] + "\n")
        print(f"Verified source archive: {entry['name']}", flush=True)
    for entry in manifest["files"]:
        fetch(entry["url"], CACHE / "sources" / entry["name"], entry["sha256"])
    if args.fetch_only:
        return
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Create and activate a disposable venv before installing reproduction dependencies")
    pip = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--no-compile"]
    # Lock contains the runtime/test imports used by these seams, not all SDK extras.
    subprocess.run(pip + ["--no-deps", "-r", str(ROOT / "experiments/requirements.lock")], check=True)
    for entry in manifest["archives"]:
        package = CACHE / "vendor" / entry["directory"]
        if entry["name"] == "fastmcp":
            package /= "fastmcp_slim"
        subprocess.run(pip + ["--no-deps", str(package)], check=True)
    subprocess.run(pip + ["--no-deps", str(ROOT)], check=True)


if __name__ == "__main__":
    main()
