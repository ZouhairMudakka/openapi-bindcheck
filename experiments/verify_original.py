"""Fail closed if the recorded bounded experiment does not match the claims."""
import json
from layout import RESULTS
EXPECTED_IDS = {
    "adk": {"array_alias", "array_noncollision", "array_body_only", "array_query_omitted",
            "suffix_recollision", "duplicate_noncollision", "keycloak_realm_rename"},
    "openwebui": {"path_body_distinct", "path_body_same_value", "path_body_renamed", "keycloak_realm_rename"},
    "fastmcp": {"array_alias", "suffix_recollision", "path_body_distinct", "keycloak_realm_rename"},
}
records = {}
for adapter, wanted in EXPECTED_IDS.items():
    result = json.loads((RESULTS / f"{adapter}-original.json").read_text(encoding="utf-8"))
    cases = result["cases"]
    assert len(cases) == len(wanted)
    assert {r["case_id"] for r in cases} == wanted
    for row in cases:
        assert not row.get("error"), row
        assert row["schema_validation_error"] is None, row["schema_validation_error"]
        assert len(row["wire_requests"]) == 1
        records[adapter, row["case_id"]] = row


def wire(adapter, case):
    return records[adapter, case]["wire_requests"][0]


def matches(row):
    actual = row["wire_requests"][0]
    for key, expected in row["intended"].items():
        if key == "header":
            headers = {k.lower(): v for k, v in actual["headers"].items()}
            if any(headers.get(k.lower()) != value for k, value in expected.items()):
                return False
        elif key == "absent_headers":
            headers = {k.lower() for k in actual["headers"]}
            if any(name.lower() in headers for name in expected):
                return False
        elif actual[key] != expected:
            return False
    return True


failures = []
for (adapter, case), row in records.items():
    if adapter != "fastmcp" and not matches(row):
        failures.append(f"{adapter}/{case}")
assert set(failures) == {"adk/array_alias", "adk/array_query_omitted", "adk/suffix_recollision",
                         "openwebui/path_body_distinct", "openwebui/keycloak_realm_rename"}, failures

# Exact failure signatures: avoid accepting any arbitrary failure as evidence.
for case in ("array_alias", "array_query_omitted"):
    assert wire("adk", case)["body_text"] == ""
assert wire("adk", "array_alias")["query"] == {"array": ["QUERY_SENTINEL"]}
assert wire("adk", "array_query_omitted")["query"] == {}
assert wire("adk", "suffix_recollision")["query"] == {}
assert wire("adk", "suffix_recollision")["headers"]["x_0"] == "HEADER_SENTINEL"
assert wire("openwebui", "path_body_distinct")["body"] == {"id": "PATH_SENTINEL", "note": "NOTE_SENTINEL"}
assert wire("openwebui", "keycloak_realm_rename")["path"] == "/admin/realms/OLD_REALM"
assert wire("openwebui", "keycloak_realm_rename")["body"] == {"realm": "OLD_REALM"}

# Independent positive implementation preserves every intended location value.
assert wire("fastmcp", "array_alias")["query"] == {"array": ["QUERY_SENTINEL"]}
assert wire("fastmcp", "array_alias")["body"] == ["BODY_SENTINEL"]
assert wire("fastmcp", "suffix_recollision")["path"] == "/probe/PATH_SENTINEL"
assert wire("fastmcp", "suffix_recollision")["query"] == {"x": ["QUERY_SENTINEL"]}
assert wire("fastmcp", "suffix_recollision")["headers"]["x_0"] == "HEADER_SENTINEL"
assert wire("fastmcp", "path_body_distinct")["path"] == "/probe/PATH_SENTINEL"
assert wire("fastmcp", "path_body_distinct")["body"] == {"id": "BODY_SENTINEL", "note": "NOTE_SENTINEL"}
assert wire("fastmcp", "keycloak_realm_rename")["path"] == "/admin/realms/OLD_REALM"
assert wire("fastmcp", "keycloak_realm_rename")["body"] == {"realm": "NEW_REALM"}
assert wire("fastmcp", "keycloak_realm_rename")["method"] == "PUT"
assert wire("adk", "keycloak_realm_rename")["method"] == "PUT"
print("15 exact records verified: 5 expected loss witnesses; 10 working controls/positive baselines; 0 schema or runtime errors.")
