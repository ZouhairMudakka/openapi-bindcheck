"""Independent public-call controls for the two pinned ADK diagnostic repairs.

Six parameter-order permutations preserve distinct source-location values. A
seventh call must retain the upstream dot-segment guard and emit no HTTP request.
"""
import asyncio
import hashlib
import itertools
import json
import os
from pathlib import Path
import threading

import probe
from adk_repairs import install
from layout import ADK_PIN, result_path


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


async def main():
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    from google.adk.tools.openapi_tool import OpenAPIToolset
    from google.adk.tools.openapi_tool.openapi_spec_parser import operation_parser, rest_api_tool

    # install checks each original module against its pinned whole-file SHA256
    # before changing methods in memory. The full runner also verifies packages.
    install("both")
    hashes = {name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
              for module, name in ((operation_parser, "operation_parser"), (rest_api_tool, "rest_api_tool"))}
    server = probe.ThreadingHTTPServer(("127.0.0.1", 0), probe.Echo)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    rows = []
    try:
        parts = [probe.param("x", "path", required=True), probe.param("x", "query"), probe.param("x_0", "header")]
        intended = {"path:x": "P", "query:x": "Q", "header:x_0": "H"}
        for index, order in enumerate(itertools.permutations(parts)):
            tool = (await OpenAPIToolset(spec_dict=probe.spec(list(order), path="/probe/{x}", base=base)).get_tools())[0]
            parameters = tool._operation_parser.get_parameters()
            args = {p.py_name: intended[p.param_location + ":" + p.original_name] for p in parameters}
            require(len(args) == 3, "Lost independent source slot under parameter permutation")
            start = len(probe.Echo.records)
            await tool.run_async(args=args, tool_context=None)
            requests = probe.Echo.records[start:]
            require(len(requests) == 1, "Expected exactly one HTTP request for a valid permutation")
            wire = requests[0]
            require(wire["method"] == "POST" and wire["path"] == "/probe/P"
                    and wire["query"] == {"x": ["Q"]} and wire["body"] is None,
                    "Parameter permutation changed method, path, query, or body")
            require({k.lower(): v for k, v in wire["headers"].items()}.get("x_0") == "H",
                    "Reserved original header name lost its own value")
            rows.append({"id": f"reserved_name_order_{index}", "order": [p["in"] for p in order],
                         "arguments": args, "wire": wire, "pass": True})

        document = probe.spec([probe.param("x", "path", required=True), probe.param("array", "query")],
                              {"type": "array", "items": {"type": "string"}}, path="/probe/{x}", base=base)
        tool = (await OpenAPIToolset(spec_dict=document).get_tools())[0]
        values = {"path:x": "../outside", "query:array": "Q", "body:array": ["B"]}
        args = {p.py_name: values[p.param_location + ":" + p.original_name] for p in tool._operation_parser.get_parameters()}
        start = len(probe.Echo.records)
        result = await tool.run_async(args=args, tool_context=None)
        requests = probe.Echo.records[start:]
        require(requests == [], "Dot-segment path reached HTTP transport")
        require(isinstance(result, dict) and isinstance(result.get("error"), str)
                and "parent-directory" in result["error"], "Expected the native path-validation error")
        rows.append({"id": "dot_segment_rejection_with_array_alias", "return_value": result,
                     "wire": requests, "pass": True})
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    output = {"mode": "both", "source_pin": ADK_PIN, "source_hashes": hashes,
              "passed": len(rows), "total": 7, "cases": rows}
    require(len(rows) == 7, "Independent control set is incomplete")
    result_path("controls.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("Independent ADK public-call controls: 7/7 passed")


if __name__ == "__main__":
    asyncio.run(main())
