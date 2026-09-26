"""Ablation against the real ADK tool interface and a local HTTP witness."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import threading

import probe
from adk_repairs import install

from layout import CACHE, RESULTS, ADK_PIN
from openapi_bindcheck.oracle import check_request


def fixtures(base):
    cases = []
    for name, document, _, expected in probe.array_cases(base):
        values = {"body:array": [probe.S["body"]]}
        if expected["query"]:
            key = next(iter(expected["query"]))
            values["query:" + key] = probe.S["query"]
        cases.append((name, document, values, expected))
    for name, document, _, expected in probe.alias_cases(base):
        header_name = next(iter(expected["header"]))
        values = {"path:x": probe.S["path"], "query:x": probe.S["query"], "header:" + header_name: probe.S["header"]}
        cases.append((name, document, values, expected))
    document = probe.spec([probe.param("array", "query"), probe.param("array_0", "header")], {"type": "array", "items": {"type": "string"}}, base=base)
    cases.append(("combined_alias_and_body", document,
                  {"query:array": probe.S["query"], "header:array_0": probe.S["header"], "body:array": [probe.S["body"]]},
                  {"query": {"array": [probe.S["query"]]}, "header": {"array_0": probe.S["header"]}, "body": [probe.S["body"]]}))
    document = probe.spec([probe.param("array", "query")], {"type": "array", "items": {"type": "string"}}, base=base)
    cases.append(("empty_array_alias", document, {"body:array": []}, {"query": {}, "body": []}))
    return cases


def matches(wire, expected):
    return not check_request(expected, wire)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["original", "body", "aliases", "both"], required=True)
    args = parser.parse_args()
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    from google.adk.tools.openapi_tool import OpenAPIToolset
    from google.adk.tools.openapi_tool.openapi_spec_parser import operation_parser, rest_api_tool
    source_hashes = {}
    for module, name in [(operation_parser, "operation_parser"), (rest_api_tool, "rest_api_tool")]:
        actual = Path(module.__file__).read_bytes()
        captured = (CACHE / "vendor" / ("adk-python-" + ADK_PIN) / "src/google/adk/tools/openapi_tool/openapi_spec_parser" / (name + ".py")).read_bytes()
        if actual != captured:
            raise RuntimeError("Installed source differs from prior-art pin: " + name)
        source_hashes[name] = hashlib.sha256(actual).hexdigest()
    install(args.mode)
    server = probe.ThreadingHTTPServer(("127.0.0.1", 0), probe.Echo)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rows = []
    try:
        for name, document, values, expected in fixtures(f"http://127.0.0.1:{server.server_port}"):
            expected = dict(expected, method="POST", path="/probe/" + probe.S["path"] if "path:x" in values else "/probe")
            row = {"id": name, "intended_bindings": values, "expected": expected}
            start = len(probe.Echo.records)
            try:
                tool = (await OpenAPIToolset(spec_dict=document).get_tools())[0]
                parameters = tool._operation_parser.get_parameters()
                binding_map = [{"source": p.param_location + ":" + p.original_name, "argument": p.py_name} for p in parameters]
                row["binding_map"] = binding_map
                row["alias_collision"] = len({p.py_name for p in parameters}) != len(parameters)
                tool_args = {p.py_name: values[p.param_location + ":" + p.original_name] for p in parameters if p.param_location + ":" + p.original_name in values}
                row["arguments"] = tool_args
                # Collided interfaces cannot express the intended independent values.
                # Invoke the deterministic last-binding projection only as a witness;
                # this is explicitly not a valid encoding of the intended request.
                row["argument_encoding"] = "lossy diagnostic projection" if row["alias_collision"] else "complete generated binding"
                declaration = tool._get_declaration().model_dump(mode="json", exclude_none=True)
                row["schema"] = declaration.get("parameters_json_schema") or declaration.get("parameters")
                row["schema_error"] = probe.check_schema(row["schema"], tool_args)
                row["return_value"] = await tool.run_async(args=tool_args, tool_context=None)
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["wire"] = probe.Echo.records[start:]
            row["pass"] = not row.get("error") and not row.get("schema_error") and not row.get("alias_collision", True) and len(row["wire"]) == 1 and matches(row["wire"][0], expected)
            rows.append(row)
    finally:
        server.shutdown()
        server.server_close()
    result = {"mode": args.mode, "source_pin": probe.ADK_PIN, "source_hashes": source_hashes, "cases": rows}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"adk-ablation-{args.mode}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"mode": args.mode, "passed": sum(row["pass"] for row in rows), "total": len(rows), "cases": [{key: row.get(key) for key in ("id", "pass", "error", "schema_error", "alias_collision")} for row in rows]}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
