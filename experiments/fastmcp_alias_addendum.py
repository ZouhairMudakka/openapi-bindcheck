"""Gated secondary-alias collision in FastMCP; no source modification."""
import asyncio
import argparse
import json
import os
import threading
from http.server import ThreadingHTTPServer
os.environ["FASTMCP_CHECK_FOR_UPDATES"] = "off"
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
import httpx2
from fastmcp import Client, FastMCP
from layout import FASTMCP_PIN, result_path
from probe import Echo, S, check_schema, param, spec


async def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--repair", action="store_true")
    options = cli.parse_args()
    repair = None
    if options.repair:
        from fastmcp_repairs import install
        repair = install()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Echo)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    pq = [param("x", "path", required=True), param("x", "query")]
    base_args = {"x__path": S["path"], "x__query": S["query"]}
    common = {"path": "/probe/" + S["path"], "query": {"x": [S["query"]]}}
    cases = [
        ("secondary_alias_collision", pq + [param("x__path", "header")], base_args,
         {**common, "header": {"x__path": S["header"]}}),
        ("renamed_header_control", pq + [param("z", "header")], {**base_args, "z": S["header"]},
         {**common, "header": {"z": S["header"]}}),
        ("header_declaration_absent_control", pq, base_args, {**common, "header": {}, "absent_headers": ["x__path"]}),
        ("declared_header_intended_omitted", pq + [param("x__path", "header")], base_args,
         {**common, "header": {}, "absent_headers": ["x__path"]}),
    ]
    rows = []
    try:
        for case_id, params, args, intended in cases:
            if options.repair and case_id in {"secondary_alias_collision", "declared_header_intended_omitted"}:
                args = {"x__path_0": S["path"], "x__query": S["query"]}
                if case_id == "secondary_alias_collision":
                    args["x__path"] = S["header"]
            document = spec(params, path="/probe/{x}", base=base)
            row = {"case_id": case_id, "spec": document, "tool_arguments": args, "intended": intended}
            row["argument_encoding"] = (
                "lossy diagnostic projection"
                if not options.repair and case_id in {"secondary_alias_collision", "declared_header_intended_omitted"}
                else "complete generated binding"
            )
            start = len(Echo.records)
            try:
                async with httpx2.AsyncClient(base_url=base, trust_env=False) as http_client:
                    mcp = FastMCP.from_openapi(openapi_spec=document, client=http_client)
                    async with Client(mcp) as client:
                        tool = (await client.list_tools())[0]
                        row["declaration"] = tool.model_dump(mode="json", exclude_none=True)
                        row["schema_validation_error"] = check_schema(tool.input_schema, args)
                        value = await client.call_tool("probe", args)
                        row["return_value"] = value.data
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            row["wire_requests"] = Echo.records[start:]
            rows.append(row)
    finally:
        server.shutdown()
        server.server_close()
    output = {"source_pin": FASTMCP_PIN, "repair": repair, "seam": "actual FastMCP.from_openapi + Client.list_tools/call_tool, loopback HTTP echo", "cases": rows}
    output_name = "fastmcp-suffix-corrected.json" if options.repair else "fastmcp-suffix-addendum.json"
    result_path(output_name).write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    for row in rows:
        assert not row.get("error"), row
        assert row["schema_validation_error"] is None, row
        assert len(row["wire_requests"]) == 1
        actual = row["wire_requests"][0]
        assert actual["query"] == {"x": [S["query"]]}
        if options.repair:
            assert actual["path"] == row["intended"]["path"]
            for key, value in row["intended"]["header"].items():
                assert actual["headers"][key] == value
            for key in row["intended"].get("absent_headers", []):
                assert key not in actual["headers"]
        elif row["case_id"] in {"secondary_alias_collision", "declared_header_intended_omitted"}:
            assert actual["path"] == "/probe/%7Bx%7D"
            assert actual["headers"]["x__path"] == S["path"]
        else:
            assert actual["path"] == "/probe/" + S["path"]
            assert "x__path" not in actual["headers"]
            if row["case_id"] == "renamed_header_control":
                assert actual["headers"]["z"] == S["header"]
        print(row["case_id"], json.dumps({"path": actual["path"], "query": actual["query"],
                                        "header": {k: v for k, v in actual["headers"].items() if k in {"x__path", "z"}}}))


if __name__ == "__main__":
    asyncio.run(main())
