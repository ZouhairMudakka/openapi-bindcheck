"""Diagnostic corrections to two pinned ADK component methods, for comparison.

These are conventional binding repairs, not a new algorithm. Upstream source is
loaded from the installed, separately attributed Apache-2.0 ADK distribution.
"""
import hashlib
from pathlib import Path
import inspect
import textwrap


def unique_names(self):
    reserved = {parameter.py_name for parameter in self._params}
    allocated = set()
    for parameter in self._params:
        base = parameter.py_name
        alias = base
        suffix = 0
        while alias in allocated:
            alias = f"{base}_{suffix}"
            suffix += 1
            if alias in reserved:
                alias = base
        parameter.py_name = alias
        allocated.add(alias)


def install(mode):
    from google.adk.tools.openapi_tool.openapi_spec_parser import operation_parser, rest_api_tool
    for module, digest in [(operation_parser, 'ca49cbc9ba52f274403afb6717dab93424f1bdc93085ad8d82f99df6e1a1b82b'), (rest_api_tool, 'be1d70081c7ff35eb83647d80a559b45b5d3d3a75c478198b97b7690c484ff1f')]:
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Diagnostic correction requires the pinned original source")
    if mode in {"aliases", "both"}:
        operation_parser.OperationParser._dedupe_param_names = unique_names
    if mode in {"body", "both"}:
        method = rest_api_tool.RestApiTool._prepare_request_params
        source = textwrap.dedent(inspect.getsource(method))
        replacements = {
            'param.param_location == "body" and param.py_name == "array"': 'param.param_location == "body" and param.original_name == "array"',
            'body_data = kwargs.get("array")': 'body_data = kwargs.get(param.py_name)',
        }
        for old, new in replacements.items():
            if source.count(old) != 1:
                raise RuntimeError("Pinned method shape changed; refusing diagnostic patch")
            source = source.replace(old, new)
        namespace = dict(rest_api_tool.__dict__)
        exec(compile(source, "<diagnostic-array-binding-correction>", "exec"), namespace)
        rest_api_tool.RestApiTool._prepare_request_params = namespace["_prepare_request_params"]
