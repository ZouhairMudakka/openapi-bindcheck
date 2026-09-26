"""Compare an intended request to a captured HTTP request.

Fixtures author expectations independently of adapter parameter maps. Headers
can be required or forbidden; other transport headers are ignored. JSON equality
is structural and type-sensitive (including int versus float). This oracle does
not infer business semantics or execute a server.
"""


def _equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def check_request(expected: dict, observed: dict) -> list[str]:
    failures = []
    supported = {"method", "path", "query", "body", "header", "absent_headers"}
    unknown = set(expected) - supported
    if unknown:
        raise ValueError(f"Unsupported expectation fields: {sorted(unknown)}")
    if not expected:
        raise ValueError("An empty expectation cannot establish request fidelity")
    headers = {name.lower(): value for name, value in observed.get("headers", {}).items()}
    for field, intended in expected.items():
        if field == "header":
            for name, value in intended.items():
                if name.lower() not in headers or not _equal(headers[name.lower()], value):
                    failures.append(f"header:{name}")
        elif field == "absent_headers":
            failures.extend(f"unexpected_header:{name}" for name in intended if name.lower() in headers)
        elif field not in observed or not _equal(observed[field], intended):
            failures.append(field)
    return failures


def evaluate_case(case: dict) -> dict:
    """Normalize original and ablation records without trusting reported pass bits."""
    identity = case.get("case_id", case.get("id"))
    expected = case.get("intended", case.get("expected"))
    if not identity or expected is None:
        raise ValueError("Case needs an id and independently authored expectation")
    # Validate the contract even when dispatch failed before a request was sent.
    check_request(expected, {})
    wire = case.get("wire_requests", case.get("wire", []))
    failures = []
    if case.get("error"):
        failures.append("adapter_error")
    if case.get("schema_validation_error", case.get("schema_error")):
        failures.append("invalid_tool_arguments")
    if case.get("alias_collision"):
        failures.append("unrepresentable_bindings")
    if len(wire) != 1:
        failures.append("request_count")
    else:
        failures.extend(check_request(expected, wire[0]))
    return {"id": identity, "pass": not failures, "failures": failures}
