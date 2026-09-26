"""Bounded component reproduction; authored fixtures, no model or external calls."""
from __future__ import annotations

import argparse
import ast
import asyncio
import base64
import copy
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlsplit

from layout import ADK_PIN, CACHE, FASTMCP_PIN, OPENWEBUI_PIN, ROOT, RESULTS, result_path

# Retained aliases for the other experiment scripts importing probe.
FM_PIN = FASTMCP_PIN
OW_PIN = OPENWEBUI_PIN
S = {"path": "PATH_SENTINEL", "query": "QUERY_SENTINEL", "header": "HEADER_SENTINEL", "body": "BODY_SENTINEL"}


def param(name, location, *, required=False):
    return {"name": name, "in": location, "required": required, "schema": {"type": "string"}}


def spec(parameters, body=None, path="/probe", base="http://127.0.0.1"):
    operation = {"operationId": "probe", "parameters": parameters, "responses": {"200": {"description": "Echo"}}}
    if body is not None:
        operation["requestBody"] = {"required": True, "content": {"application/json": {"schema": body}}}
    return {"openapi": "3.0.3", "info": {"title": "Authored binding fixture", "version": "1"},
            "servers": [{"url": base}], "paths": {path: {"post": operation}}}


def array_cases(base):
    array = {"type": "array", "title": "Array", "items": {"type": "string"}}
    return [
        ("array_alias", spec([param("array", "query")], array, base=base),
         {"array": S["query"], "array_0": [S["body"]]}, {"query": {"array": [S["query"]]}, "body": [S["body"]]}),
        ("array_noncollision", spec([param("group", "query")], array, base=base),
         {"group": S["query"], "array": [S["body"]]}, {"query": {"group": [S["query"]]}, "body": [S["body"]]}),
        ("array_body_only", spec([], array, base=base),
         {"array": [S["body"]]}, {"query": {}, "body": [S["body"]]}),
        ("array_query_omitted", spec([param("array", "query")], array, base=base),
         {"array_0": [S["body"]]}, {"query": {}, "body": [S["body"]]}),
    ]


def alias_cases(base):
    return [
        ("suffix_recollision", spec([param("x", "path", required=True), param("x", "query"), param("x_0", "header")], path="/probe/{x}", base=base),
         {"x": S["path"], "x_0": S["header"]},
         {"path": "/probe/" + S["path"], "query": {"x": [S["query"]]}, "header": {"x_0": S["header"]}}),
        ("duplicate_noncollision", spec([param("x", "path", required=True), param("x", "query"), param("z", "header")], path="/probe/{x}", base=base),
         {"x": S["path"], "x_0": S["query"], "z": S["header"]},
         {"path": "/probe/" + S["path"], "query": {"x": [S["query"]]}, "header": {"z": S["header"]}}),
    ]


def flat_cases(base):
    def body(name):
        return {"type": "object", "properties": {name: {"type": "string"}, "note": {"type": "string"}},
                "required": [name, "note"], "additionalProperties": False}
    return [
        ("path_body_distinct", spec([param("id", "path", required=True)], body("id"), "/probe/{id}", base),
         {"id": S["path"], "note": "NOTE_SENTINEL"},
         {"path": "/probe/" + S["path"], "body": {"id": S["body"], "note": "NOTE_SENTINEL"}}),
        ("path_body_same_value", spec([param("id", "path", required=True)], body("id"), "/probe/{id}", base),
         {"id": S["path"], "note": "NOTE_SENTINEL"},
         {"path": "/probe/" + S["path"], "body": {"id": S["path"], "note": "NOTE_SENTINEL"}}),
        ("path_body_renamed", spec([param("id", "path", required=True)], body("body_id"), "/probe/{id}", base),
         {"id": S["path"], "body_id": S["body"], "note": "NOTE_SENTINEL"},
         {"path": "/probe/" + S["path"], "body": {"body_id": S["body"], "note": "NOTE_SENTINEL"}}),
    ]


def keycloak_case(base, adapter):
    source_path = CACHE / "sources" / "keycloak-openapi.json"
    raw = source_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "ba68e1c3842c11701ec64c5f3ba23387cf53963f8d16dd7c3d45da103b9421db"
    source = json.loads(raw)
    path = "/admin/realms/{realm}"
    item = source["paths"][path]
    document = {"openapi": source["openapi"], "info": source["info"],
                "servers": [{"url": base}], "components": source["components"],
                "paths": {path: {"parameters": item["parameters"], "put": copy.deepcopy(item["put"])}}}
    # The real spec omits an operationId. Both tool systems need one to expose it.
    # Only an operationId and local server URL are authored; parameter/body schemas are preserved.
    document["paths"][path]["put"]["operationId"] = "probe"
    arguments = {"realm": "OLD_REALM"}
    if adapter == "adk":
        arguments["realm_0"] = "NEW_REALM"
    elif adapter == "fastmcp":
        arguments = {"realm": "NEW_REALM", "realm__path": "OLD_REALM"}
    return ("keycloak_realm_rename", document, arguments,
            {"path": "/admin/realms/OLD_REALM", "body": {"realm": "NEW_REALM"}})


class Echo(BaseHTTPRequestHandler):
    records = []

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        record = {"method": self.command, "raw_target": self.path, "path": urlsplit(self.path).path,
                  "query": parse_qs(urlsplit(self.path).query, keep_blank_values=True),
                  "headers": dict(self.headers), "body_text": raw.decode(),
                  "body": json.loads(raw) if raw else None}
        self.records.append(record)
        data = json.dumps({"echo": record}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_PUT = do_POST

    def log_message(self, *_):
        pass


def check_schema(schema, args):
    from jsonschema import Draft202012Validator
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(args)
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


async def adk(base):
    import google.adk.tools.openapi_tool.openapi_spec_parser.rest_api_tool as module
    from google.adk.tools.openapi_tool import OpenAPIToolset
    rows = []
    for case_id, document, args, intended in array_cases(base) + alias_cases(base) + [keycloak_case(base, "adk")]:
        start = len(Echo.records)
        row = {"case_id": case_id, "spec": document, "tool_arguments": args, "intended": intended}
        row["argument_encoding"] = "lossy diagnostic projection" if case_id == "suffix_recollision" else "complete generated binding"
        try:
            toolset = OpenAPIToolset(spec_dict=document)
            tool = (await toolset.get_tools())[0]
            declaration = tool._get_declaration().model_dump(mode="json", exclude_none=True)
            schema = declaration.get("parameters_json_schema") or declaration.get("parameters")
            row["declaration"] = declaration
            row["parameters"] = [{"original_name": p.original_name, "location": p.param_location, "argument_name": p.py_name}
                                 for p in tool._operation_parser.get_parameters()]
            row["schema_validation_error"] = check_schema(schema, args)
            row["return_value"] = await tool.run_async(args=args.copy(), tool_context=None)
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["wire_requests"] = Echo.records[start:]
        rows.append(row)
    return {"source_pin": ADK_PIN, "import_path": module.__name__.replace(".", "/") + ".py",
            "import_source_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(), "cases": rows}


def openwebui_functions():
    """Unmodified upstream function ASTs, not full Open WebUI app initialization.

    Only framework-global constants and stdlib/aiohttp dependencies are provided.
    There are no database/auth/user/app calls on the selected paths. This remains
    a component reproduction, not a full-chat or whole-app test.
    """
    import aiohttp
    path = CACHE / "sources" / "ow-tools.py"
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != "ae4fc82448f914863a770bb105591f5c161a372b16bcbf40014f22b28c8bc9b9":
        raise RuntimeError("Open WebUI source differs from the pinned component")
    wanted = {"resolve_schema", "convert_openapi_to_tool_payload", "execute_tool_server"}
    selected = [node for node in ast.parse(source).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted]
    assert {node.name for node in selected} == wanted
    namespace = {"Any": Any, "aiohttp": aiohttp, "quote": quote, "urlencode": urlencode, "copy": copy,
                 "base64": base64, "log": logging.getLogger("openwebui-component-probe"),
                 "OPENAPI_HTTP_METHODS": {"get", "put", "post", "delete", "options", "head", "patch", "trace"},
                 "AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER": 10,
                 "AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL": True, "AIOHTTP_CLIENT_ALLOW_REDIRECTS": False}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "<pinned-openwebui-tools-component>", "exec"), namespace)
    return namespace, hashlib.sha256(source).hexdigest()


async def openwebui(base):
    ns, digest = openwebui_functions()
    rows = []
    for case_id, document, args, intended in flat_cases(base) + [keycloak_case(base, "openwebui")]:
        start = len(Echo.records)
        row = {"case_id": case_id, "spec": document, "tool_arguments": args, "intended": intended}
        row["argument_encoding"] = "lossy diagnostic projection" if case_id in {"path_body_distinct", "keycloak_realm_rename"} else "complete generated binding"
        try:
            declaration = ns["convert_openapi_to_tool_payload"](document)[0]
            row["declaration"] = declaration
            row["schema_validation_error"] = check_schema(declaration["parameters"], args)
            value, headers = await ns["execute_tool_server"](base, {}, {}, "probe", args.copy(), {"openapi": document})
            row["return_value"] = value
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["wire_requests"] = Echo.records[start:]
        rows.append(row)
    return {"source_pin": OW_PIN, "source_sha256": digest,
            "seam": "Unmodified AST for the three upstream functions; real aiohttp and local HTTP server; not full app import", "cases": rows}


async def fastmcp(base):
    import httpx2
    from fastmcp import Client, FastMCP
    import fastmcp
    rows = []
    fixtures = [
        ("array_alias", spec([param("array", "query")], {"type": "array", "title": "Array", "items": {"type": "string"}}, base=base),
         {"array": [S["body"]], "array__query": S["query"]}, array_cases(base)[0][3]),
        ("suffix_recollision", alias_cases(base)[0][1], {"x__path": S["path"], "x__query": S["query"], "x_0": S["header"]}, alias_cases(base)[0][3]),
        ("path_body_distinct", flat_cases(base)[0][1], {"id": S["body"], "id__path": S["path"], "note": "NOTE_SENTINEL"}, flat_cases(base)[0][3]),
    ]
    fixtures.append(keycloak_case(base, "fastmcp"))
    for case_id, document, args, intended in fixtures:
        start = len(Echo.records)
        row = {"case_id": case_id, "spec": document, "tool_arguments": args, "intended": intended,
               "argument_encoding": "complete generated binding"}
        try:
            async with httpx2.AsyncClient(base_url=base, trust_env=False) as http_client:
                server = FastMCP.from_openapi(openapi_spec=document, client=http_client)
                async with Client(server) as client:
                    tool = (await client.list_tools())[0]
                    row["declaration"] = tool.model_dump(mode="json", exclude_none=True)
                    row["schema_validation_error"] = check_schema(tool.input_schema, args)
                    value = await client.call_tool("probe", args)
                    row["return_value"] = value.data
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["wire_requests"] = Echo.records[start:]
        rows.append(row)
    return {"source_pin": FM_PIN, "import_path": "fastmcp/__init__.py",
            "import_source_sha256": hashlib.sha256(Path(fastmcp.__file__).read_bytes()).hexdigest(), "cases": rows}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=["adk", "openwebui", "fastmcp"], required=True)
    parser.add_argument("--output", type=Path, help="Output filename under BINDCHECK_RESULTS (or an absolute output path)")
    args = parser.parse_args()
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["FASTMCP_CHECK_FOR_UPDATES"] = "off"
    server = ThreadingHTTPServer(("127.0.0.1", 0), Echo)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = await globals()[args.adapter](f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
        server.server_close()
    result["python"] = sys.version
    result["dependencies"] = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}
    output = result_path(args.output or f"{args.adapter}-original.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    for case in result["cases"]:
        print(case["case_id"], "error=" + str(case.get("error")), "wire=" + str(len(case["wire_requests"])))


if __name__ == "__main__":
    asyncio.run(main())
