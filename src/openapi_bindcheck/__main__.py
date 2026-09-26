import argparse
import json
from pathlib import Path

from .oracle import evaluate_case


def main():
    parser = argparse.ArgumentParser(description="Check saved OpenAPI tool-to-HTTP witnesses")
    parser.add_argument("reports", type=Path, nargs="+")
    parser.add_argument("--require-all", action="store_true", help="Exit 1 if any recorded case fails; original defects are expected to fail")
    args = parser.parse_args()
    summaries = []
    for path in args.reports:
        data = json.loads(path.read_text(encoding="utf-8"))
        cases = [evaluate_case(case) for case in data["cases"]]
        if not cases:
            raise ValueError(f"Empty case collection: {path}")
        summaries.append({"report": path.name, "passed": sum(case["pass"] for case in cases), "total": len(cases), "cases": cases})
    print(json.dumps(summaries, indent=2))
    if args.require_all and any(summary["passed"] != summary["total"] for summary in summaries):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
