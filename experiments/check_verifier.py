"""Adversarial checks of the fixed experiment verifier using saved local reports.

These mutations test rejection, not report authenticity. No source, report, or
vendor file is modified; only this check's result JSON is written.
"""
import copy
import hashlib
import json

from jsonschema.exceptions import SchemaError, ValidationError

from layout import RESULTS, result_path
from verify_results import definitions, verify_reports


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def row(reports, filename="adk-ablation-both.json", case_id="array_alias"):
    return next(item for item in reports[filename]["cases"] if item.get("id", item.get("case_id")) == case_id)


def change_body(reports, *, edit_expectation):
    case = row(reports)
    case["wire"][0].update(body=["FORGED"], body_text='["FORGED"]')
    case["pass"] = True
    if edit_expectation:
        case["expected"]["body"] = ["FORGED"]
    else:
        # Removing the saved contract must not weaken the verifier's own one.
        case["expected"] = {}


def change_method(reports):
    case = row(reports)
    case["wire"][0]["method"] = "GET"
    case["expected"]["method"] = "GET"
    case["pass"] = True


def alternate_failure(reports):
    # This still fails the intended request, but no longer witnesses the claimed
    # array omission. A verifier of counts alone would accept it.
    case = row(reports, "adk-ablation-original.json")
    case["wire"][0].update(body=["UNRELATED-FAILURE"], body_text='["UNRELATED-FAILURE"]')
    case["pass"] = False


def present_json_null(reports):
    # Parsed None alone cannot establish that the HTTP body was absent.
    row(reports, "adk-ablation-original.json")["wire"][0]["body_text"] = "null"


def conceal_collision(reports):
    case = row(reports, "adk-ablation-original.json", "suffix_recollision")
    case["alias_collision"] = False
    case["argument_encoding"] = "complete generated binding"
    for index, binding in enumerate(case["binding_map"]):
        binding["argument"] = f"invented_{index}"


def make_invalid_arguments(reports):
    case = row(reports)
    case["arguments"] = {"not_an_exposed_required_path": object.__name__}
    # Make the captured declaration explicitly reject these arguments. Merely
    # retaining schema_error=None must not override actual schema validation.
    case["schema"] = {"type": "object", "properties": {}, "additionalProperties": False}
    case["schema_error"] = None


def duplicate_case(reports):
    cases = reports["adk-ablation-both.json"]["cases"]
    cases[-1] = copy.deepcopy(cases[0])


def leak_omitted_header(reports):
    case = row(reports, "fastmcp-suffix-corrected.json", "declared_header_intended_omitted")
    case["wire_requests"][0]["headers"]["x__path"] = "UNINTENDED"
    case["intended"]["absent_headers"] = []
    case["pass"] = True


def main():
    reports, hashes = {}, {}
    for filename in definitions():
        raw = (RESULTS / filename).read_bytes()
        reports[filename] = json.loads(raw)
        hashes[filename] = hashlib.sha256(raw).hexdigest()
    baseline = verify_reports(reports)
    require(baseline.get("verified") is True and baseline.get("report_count") == 9,
            "Baseline reports must verify before mutation tests")

    # A saved pass flag has no authority in either direction.
    forged_flags = copy.deepcopy(reports)
    for report in forged_flags.values():
        for case in report["cases"]:
            case["pass"] = not case.get("pass", False)
    require(verify_reports(forged_flags) == baseline, "Saved pass flags changed recomputed verdicts")

    mutations = {
        "request_and_expected_body_both_forged": lambda data: change_body(data, edit_expectation=True),
        "request_body_forged_saved_contract_empty": lambda data: change_body(data, edit_expectation=False),
        "request_and_expected_method_both_forged": change_method,
        "different_failure_same_failed_case": alternate_failure,
        "json_null_disguised_as_absent_body": present_json_null,
        "omitted_header_leaked_expected_absence_erased": leak_omitted_header,
        "missing_case": lambda data: data["adk-ablation-both.json"]["cases"].pop(),
        "duplicate_case_preserving_count": duplicate_case,
        "missing_report": lambda data: data.pop("adk-ablation-both.json"),
        "wrong_source_pin": lambda data: data["adk-ablation-both.json"].update(source_pin="0" * 40),
        "wrong_mode": lambda data: data["adk-ablation-both.json"].update(mode="original"),
        "concealed_alias_collision": conceal_collision,
        "missing_schema_validation": lambda data: row(data).pop("schema_error"),
        "invalid_arguments_despite_no_recorded_schema_error": make_invalid_arguments,
        "no_request": lambda data: row(data).update(wire=[]),
        "duplicate_request": lambda data: row(data)["wire"].append(copy.deepcopy(row(data)["wire"][0])),
        "raw_decoded_body_disagree": lambda data: row(data)["wire"][0].update(body_text='["OTHER"]'),
    }
    rejected = []
    for name, mutate in mutations.items():
        changed = copy.deepcopy(reports)
        mutate(changed)
        try:
            verify_reports(changed)
        except (ValueError, ValidationError, SchemaError) as exc:
            rejected.append({"id": name, "rejected": True, "error_type": type(exc).__name__,
                             "reason": str(exc).splitlines()[0]})
        else:
            raise RuntimeError(f"Verifier accepted corrupted evidence: {name}")
    output = {"verified": True, "baseline_reports": 9, "source_report_sha256": hashes,
              "saved_pass_flags_ignored": True, "mutations_rejected": len(rejected), "cases": rejected}
    result_path("verifier-controls.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Verifier controls: baseline 9 reports; saved pass flags ignored; {len(rejected)}/{len(mutations)} mutations rejected")


if __name__ == "__main__":
    main()
