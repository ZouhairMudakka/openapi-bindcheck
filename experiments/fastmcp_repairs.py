"""Diagnostic standard alias-allocation repair; pinned upstream function in memory.

Upstream FastMCP is Apache-2.0. This does not modify the source tree or package.
"""
import hashlib
import inspect
from pathlib import Path
import textwrap

SOURCE_SHA256 = "a9e69fbaab8fc0834f4c9affb168a8cfe05662af36a6859236d75ef4e0b97cd5"


def install():
    from fastmcp.utilities.openapi import parser, schemas
    source_path = Path(schemas.__file__)
    actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"Unexpected FastMCP source hash: {actual}")
    original = schemas._combine_schemas_and_map_params
    if parser._combine_schemas_and_map_params is not original:
        raise RuntimeError("Parser binding was already replaced; refusing ambiguous patch")
    source = textwrap.dedent(inspect.getsource(original))
    replacements = {
        "    # Add parameters with suffixes for collisions\n":
        "    # Reserve original names before allocating any derived alias.\n"
        "    reserved_names = all_non_body_params | body_param_names\n"
        "    allocated_names = set()\n\n"
        "    # Add parameters with suffixes for collisions\n",
        '            suffixed_name = f"{param.name}__{param.location}"\n':
        '            base_alias = f"{param.name}__{param.location}"\n'
        '            suffixed_name = base_alias\n'
        '            alias_index = 0\n'
        '            while suffixed_name in reserved_names or suffixed_name in allocated_names:\n'
        '                suffixed_name = f"{base_alias}_{alias_index}"\n'
        '                alias_index += 1\n'
        '            allocated_names.add(suffixed_name)\n',
        "            # No collision, use original name\n":
        "            # No collision, use original name\n"
        "            allocated_names.add(param.name)\n",
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise RuntimeError("Pinned allocator shape changed; refusing diagnostic patch")
        source = source.replace(old, new)
    namespace = dict(schemas.__dict__)
    exec(compile(source, "<diagnostic-fastmcp-alias-reservation>", "exec"), namespace)
    corrected = namespace["_combine_schemas_and_map_params"]
    schemas._combine_schemas_and_map_params = corrected
    parser._combine_schemas_and_map_params = corrected
    return {"original_source_sha256": actual,
            "corrected_function_sha256": hashlib.sha256(source.encode()).hexdigest()}
