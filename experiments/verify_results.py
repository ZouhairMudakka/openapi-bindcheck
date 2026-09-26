"""Verify the nine fixed reports against independently authored wire contracts.

Saved pass bits and saved expectations do not determine the outcome. These
checks establish consistency of a local reproduction, not evidence authenticity.
"""
from __future__ import annotations

import copy
import hashlib
import json
from urllib.parse import parse_qs, urlsplit

from jsonschema import Draft202012Validator

from layout import ADK_PIN, FASTMCP_PIN, OPENWEBUI_PIN, RESULTS, result_path
from openapi_bindcheck.oracle import check_request, evaluate_case

PATH_VALUE = "PATH_SENTINEL"
QUERY_VALUE = "QUERY_SENTINEL"
HEADER_VALUE = "HEADER_SENTINEL"
BODY_VALUE = "BODY_SENTINEL"
LOSSY = "lossy diagnostic projection"
COMPLETE = "complete generated binding"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def contract(*, path="/probe", query=None, body=None, header=None,
             absent_headers=None, method="POST"):
    # Every contract checks all four request dimensions, including absent bodies.
    return {"method": method, "path": path, "query": {} if query is None else query,
            "body": body, "header": {} if header is None else header,
            "absent_headers": [] if absent_headers is None else absent_headers}


ARRAY_CONTRACTS = {
    "array_alias": contract(query={"array": [QUERY_VALUE]}, body=[BODY_VALUE]),
    "array_noncollision": contract(query={"group": [QUERY_VALUE]}, body=[BODY_VALUE]),
    "array_body_only": contract(body=[BODY_VALUE]),
    "array_query_omitted": contract(body=[BODY_VALUE]),
}
ALIAS_CONTRACTS = {
    "suffix_recollision": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, header={"x_0": HEADER_VALUE}),
    "duplicate_noncollision": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, header={"z": HEADER_VALUE}),
}
KEYCLOAK = contract(method="PUT", path="/admin/realms/OLD_REALM", body={"realm": "NEW_REALM"})
FLAT_CONTRACTS = {
    "path_body_distinct": contract(path=f"/probe/{PATH_VALUE}", body={"id": BODY_VALUE, "note": "NOTE_SENTINEL"}),
    "path_body_same_value": contract(path=f"/probe/{PATH_VALUE}", body={"id": PATH_VALUE, "note": "NOTE_SENTINEL"}),
    "path_body_renamed": contract(path=f"/probe/{PATH_VALUE}", body={"body_id": BODY_VALUE, "note": "NOTE_SENTINEL"}),
}
ABLATION_CONTRACTS = {
    **ARRAY_CONTRACTS, **ALIAS_CONTRACTS,
    "combined_alias_and_body": contract(query={"array": [QUERY_VALUE]}, header={"array_0": HEADER_VALUE}, body=[BODY_VALUE]),
    "empty_array_alias": contract(body=[]),
}
FM_CONTRACTS = {
    "secondary_alias_collision": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, header={"x__path": HEADER_VALUE}),
    "renamed_header_control": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, header={"z": HEADER_VALUE}, absent_headers=["x__path"]),
    "header_declaration_absent_control": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, absent_headers=["x__path"]),
    "declared_header_intended_omitted": contract(path=f"/probe/{PATH_VALUE}", query={"x": [QUERY_VALUE]}, absent_headers=["x__path"]),
}


def definitions():
    reports = {
        "adk-original.json": {
            "pin": ADK_PIN, "kind": "primary-adk", "contracts": {**ARRAY_CONTRACTS, **ALIAS_CONTRACTS, "keycloak_realm_rename": KEYCLOAK},
            "failed": {"array_alias", "array_query_omitted", "suffix_recollision"},
            "lossy": {"suffix_recollision"}, "passed": 4,
        },
        "openwebui-original.json": {
            "pin": OPENWEBUI_PIN, "kind": "primary-ow", "contracts": {**FLAT_CONTRACTS, "keycloak_realm_rename": KEYCLOAK},
            "failed": {"path_body_distinct", "keycloak_realm_rename"},
            "lossy": {"path_body_distinct", "keycloak_realm_rename"}, "passed": 2,
        },
        "fastmcp-original.json": {
            "pin": FASTMCP_PIN, "kind": "primary-fm",
            "contracts": {"array_alias": ARRAY_CONTRACTS["array_alias"], "suffix_recollision": ALIAS_CONTRACTS["suffix_recollision"],
                          "path_body_distinct": FLAT_CONTRACTS["path_body_distinct"], "keycloak_realm_rename": KEYCLOAK},
            "failed": set(), "lossy": set(), "passed": 4,
        },
    }
    ablation_failures = {
        "original": {"array_alias", "array_query_omitted", "suffix_recollision", "combined_alias_and_body", "empty_array_alias"},
        "body": {"suffix_recollision", "combined_alias_and_body"},
        "aliases": {"array_alias", "array_query_omitted", "combined_alias_and_body", "empty_array_alias"},
        "both": set(),
    }
    for mode, expected_passes in (("original", 3), ("body", 6), ("aliases", 4), ("both", 8)):
        collisions = {"suffix_recollision", "combined_alias_and_body"} if mode in {"original", "body"} else set()
        reports[f"adk-ablation-{mode}.json"] = {
            "pin": ADK_PIN, "kind": "ablation", "mode": mode, "contracts": ABLATION_CONTRACTS,
            "failed": ablation_failures[mode], "collisions": collisions, "lossy": collisions, "passed": expected_passes,
        }
    for repaired in (False, True):
        failed = set() if repaired else {"secondary_alias_collision", "declared_header_intended_omitted"}
        name = "fastmcp-suffix-corrected.json" if repaired else "fastmcp-suffix-addendum.json"
        reports[name] = {"pin": FASTMCP_PIN, "kind": "fm-addendum", "repaired": repaired,
                         "contracts": FM_CONTRACTS, "failed": failed, "lossy": failed, "passed": 4 if repaired else 2}
    return reports


def observed_signature(definition, case_id):
    """Exact known observation, separately authored from the intended contract."""
    observed = copy.deepcopy(definition["contracts"][case_id])
    if case_id not in definition["failed"]:
        return observed
    kind = definition["kind"]
    if kind in {"primary-adk", "ablation"}:
        if case_id == "suffix_recollision":
            observed["query"] = {}
        elif case_id == "combined_alias_and_body":
            mode = definition["mode"]
            if mode in {"original", "aliases"}:
                observed["body"] = None
            if mode in {"original", "body"}:
                observed["header"] = {}
                observed["absent_headers"] = ["array_0"]
        else:
            observed["body"] = None
    elif kind == "primary-ow":
        observed["body"] = {"realm": "OLD_REALM"} if case_id == "keycloak_realm_rename" else {"id": PATH_VALUE, "note": "NOTE_SENTINEL"}
    elif kind == "fm-addendum":
        observed["path"] = "/probe/%7Bx%7D"
        observed["header"] = {"x__path": PATH_VALUE}
        observed["absent_headers"] = []
    else:
        raise ValueError(f"No authored signature for {kind}/{case_id}")
    return observed


def validate_wire(wire, label):
    require(isinstance(wire, dict), f"{label}: request must be an object")
    require(isinstance(wire.get("headers"), dict), f"{label}: missing header capture")
    require(all(isinstance(k, str) and isinstance(v, str) for k, v in wire["headers"].items()), f"{label}: malformed header capture")
    raw_target = wire.get("raw_target")
    require(isinstance(raw_target, str), f"{label}: missing raw target")
    parsed = urlsplit(raw_target)
    require(wire.get("path") == parsed.path, f"{label}: raw target and path disagree")
    require(wire.get("query") == parse_qs(parsed.query, keep_blank_values=True), f"{label}: raw target and query disagree")
    body_text = wire.get("body_text")
    require(isinstance(body_text, str), f"{label}: missing raw body")
    parsed_body = json.loads(body_text) if body_text else None
    require(not check_request({"body": parsed_body}, wire), f"{label}: raw and decoded bodies disagree")


def validate_schema(row, is_ablation, label):
    error_field = "schema_error" if is_ablation else "schema_validation_error"
    require(error_field in row and row[error_field] is None, f"{label}: schema error or missing validation result")
    if is_ablation:
        schema, arguments = row.get("schema"), row.get("arguments")
    else:
        declaration = row.get("declaration", {})
        schema = declaration.get("parameters_json_schema", declaration.get("parameters", declaration.get("input_schema")))
        arguments = row.get("tool_arguments")
    require(isinstance(schema, dict) and isinstance(arguments, dict), f"{label}: missing generated schema or supplied arguments")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(arguments)


def verify_reports(reports):
    """Pure verifier used by the runner and negative controls; does not write files."""
    known = definitions()
    require(set(reports) == set(known), "Expected exactly the nine named reproduction reports")
    summaries = []
    for filename, definition in known.items():
        report = reports[filename]
        require(isinstance(report, dict), f"{filename}: report must be an object")
        require(report.get("source_pin") == definition["pin"], f"{filename}: source pin mismatch")
        is_ablation = definition["kind"] == "ablation"
        if is_ablation:
            require(report.get("mode") == definition["mode"], f"{filename}: ablation mode mismatch")
        if definition["kind"] == "fm-addendum":
            if definition["repaired"]:
                repair = report.get("repair")
                require(isinstance(repair, dict), f"{filename}: missing repair provenance")
                require(repair.get("original_source_sha256") == "a9e69fbaab8fc0834f4c9affb168a8cfe05662af36a6859236d75ef4e0b97cd5", f"{filename}: repair source mismatch")
                require(repair.get("corrected_function_sha256") == "6644dfa89eac172ca5a0969539f0974109450c6206566b5c2d2fa0685c6e9605", f"{filename}: repair function mismatch")
            else:
                require(report.get("repair") is None, f"{filename}: original report unexpectedly repaired")
        cases = report.get("cases")
        require(isinstance(cases, list), f"{filename}: missing cases")
        id_key = "id" if is_ablation else "case_id"
        require(all(isinstance(row, dict) and isinstance(row.get(id_key), str) for row in cases), f"{filename}: malformed case identity")
        ids = [row[id_key] for row in cases]
        require(len(ids) == len(set(ids)), f"{filename}: duplicate case IDs")
        require(set(ids) == set(definition["contracts"]), f"{filename}: missing or unexpected case IDs")
        checked = []
        for row in cases:
            case_id = row[id_key]
            label = f"{filename}/{case_id}"
            require(row.get("error") is None, f"{label}: adapter error")
            validate_schema(row, is_ablation, label)
            wire = row.get("wire" if is_ablation else "wire_requests")
            require(isinstance(wire, list) and len(wire) == 1, f"{label}: expected exactly one request")
            validate_wire(wire[0], label)
            intended = definition["contracts"][case_id]
            saved_expected = row.get("expected" if is_ablation else "intended")
            require(isinstance(saved_expected, dict), f"{label}: missing reported expectation")
            # A saved partial contract may document fewer fields, but must not
            # contradict the complete contract authored in this verifier.
            for key, value in saved_expected.items():
                require(key in intended and type(value) is type(intended[key]) and value == intended[key], f"{label}: reported expectation contradicts authored {key}")
            collision = False
            if is_ablation:
                collision = case_id in definition["collisions"]
                require(type(row.get("alias_collision")) is bool and row["alias_collision"] is collision, f"{label}: wrong collision flag")
                binding_map = row.get("binding_map")
                require(isinstance(binding_map, list) and all(isinstance(p, dict) and isinstance(p.get("argument"), str) for p in binding_map), f"{label}: missing binding map")
                arguments = [p["argument"] for p in binding_map]
                require((len(arguments) != len(set(arguments))) is collision, f"{label}: binding map contradicts collision flag")
            expected_encoding = LOSSY if case_id in definition["lossy"] else COMPLETE
            require(row.get("argument_encoding") == expected_encoding, f"{label}: misleading argument-encoding label")
            normalized = {"case_id": case_id, "intended": intended, "wire_requests": wire,
                          "error": None, "schema_validation_error": None, "alias_collision": collision}
            verdict = evaluate_case(normalized)
            require(verdict["pass"] is (case_id not in definition["failed"]), f"{label}: changed contract outcome: {verdict['failures']}")
            signature = observed_signature(definition, case_id)
            require(not check_request(signature, wire[0]), f"{label}: changed failure/control signature: {check_request(signature, wire[0])}")
            if signature["body"] is None:
                require(wire[0]["body_text"] == "", f"{label}: expected an absent body, not JSON null")
            checked.append(verdict)
        passed = sum(row["pass"] for row in checked)
        failed = sorted(row["id"] for row in checked if not row["pass"])
        require(passed == definition["passed"] and set(failed) == definition["failed"], f"{filename}: count or failure-ID mismatch")
        summaries.append({"report": filename, "checked": len(checked), "passed": passed, "failed": len(failed),
                          "failed_case_ids": failed, "cases": checked})
    return {"verified": True, "report_count": len(summaries), "reports": summaries,
            "caveat": "Cases overlap across primary reports, controls, and ablations. These counts are diagnostic fixture coverage, not independent samples, production failure rates, or framework rankings.",
            "scope": "Pinned component/tool-to-wire observations; Open WebUI uses unchanged extracted functions, and Keycloak is a schema-derived local wire specimen, not a live server test."}


def main():
    summary_path = result_path("summary.json")
    summary_path.unlink(missing_ok=True)
    reports, hashes = {}, {}
    for filename in definitions():
        raw = (RESULTS / filename).read_bytes()
        reports[filename] = json.loads(raw)
        hashes[filename] = hashlib.sha256(raw).hexdigest()
    summary = verify_reports(reports)
    summary["report_sha256"] = hashes
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verified": True, "reports": [{key: report[key] for key in ("report", "checked", "passed", "failed")} for report in summary["reports"]]}, indent=2))


if __name__ == "__main__":
    main()
