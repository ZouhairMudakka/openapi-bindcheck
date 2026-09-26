"""Export portable reference JSON after a successful complete reproduction.

The sole wire normalization replaces ephemeral loopback ports with port 0, in
URLs/Host headers and echoed values. Source bytes and request values are not
otherwise transformed. Reference files are observations, not live replay input.
"""
import hashlib
import json
import re

from layout import ROOT, RESULTS


def normalize(value):
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"127\.0\.0\.1:\d+", "127.0.0.1:0", value)
    return value


def main():
    status = json.loads((RESULTS / "run-status.json").read_text())
    if not status.get("success") or not status.get("native_requested"):
        raise RuntimeError("Reference export requires successful reproduce.py --native")
    target = ROOT / "results/reference"
    target.mkdir(parents=True, exist_ok=True)
    files = {}
    for path in sorted(RESULTS.glob("*.json")):
        # Summary input hashes identify original raw observations; retain those
        # hashes, with exported/normalized bytes separately indexed below.
        value = normalize(json.loads(path.read_text(encoding="utf-8")))
        data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
        (target / path.name).write_bytes(data)
        files[path.name] = {"raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "reference_sha256": hashlib.sha256(data).hexdigest()}
    (target / "manifest.json").write_text(json.dumps({"normalization": "ephemeral 127.0.0.1 ports replaced with 0; summary input hashes identify raw bytes", "files": files}, indent=2) + "\n")
    print(f"Exported {len(files)} JSON reports to results/reference")


if __name__ == "__main__":
    main()
