"""Run each diagnostic mode in a fresh interpreter; fail on a changed finding."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from layout import ROOT, CACHE, RESULTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="Also run the unchanged selected upstream test modules in both modes")
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").unlink(missing_ok=True)
    status_path = RESULTS / "run-status.json"
    status_path.write_text(json.dumps({"success": False, "native_requested": args.native}) + "\n")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "FASTMCP_CHECK_FOR_UPDATES": "off",
           "PYTHONOPTIMIZE": "",
           "PYTHONUTF8": "1",
           "BINDCHECK_CACHE": str(CACHE), "BINDCHECK_RESULTS": str(RESULTS),
           "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    commands = [["provenance.py"]]
    commands += [["probe.py", "--adapter", adapter, "--output", str(RESULTS / f"{adapter}-original.json")]
                 for adapter in ("adk", "openwebui", "fastmcp")]
    commands += [["verify_original.py"]]
    commands += [["run_corrections.py", "--mode", mode] for mode in ("original", "body", "aliases", "both")]
    commands += [["fastmcp_alias_addendum.py"], ["fastmcp_alias_addendum.py", "--repair"], ["controls.py"], ["verify_results.py"], ["check_verifier.py"]]
    if args.native:
        commands += [["native_tests.py", "--adapter", adapter] + repair
                     for adapter in ("adk", "fastmcp") for repair in ([], ["--repair"])]
    for index, command in enumerate(commands):
        label = " ".join(command)
        print(f"[{index+1}/{len(commands)}] {label}", flush=True)
        log = RESULTS / f"run-{index+1:02d}-{Path(command[0]).stem}.log"
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run([sys.executable, "-B", str(ROOT / "experiments" / command[0]), *command[1:]],
                                    cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text(encoding="utf-8")[-12000:])
            raise SystemExit(f"Failed: {label}; full output: {log}")
    status_path.write_text(json.dumps({"success": True, "native_requested": args.native, "steps_completed": len(commands)}) + "\n")
    summary = json.loads((RESULTS / "summary.json").read_text())
    print(json.dumps({"verified": summary["verified"], "reports": [
        {key: report[key] for key in ("report", "checked", "passed", "failed")}
        for report in summary["reports"]]}, indent=2))


if __name__ == "__main__":
    main()
