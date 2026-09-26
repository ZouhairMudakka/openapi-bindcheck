# Prior art, contribution, and evidence

Reviewed on **27 September 2026**. These findings concern pinned source revisions, not every past or future release.

## What this project contributes

`openapi-bindcheck` contributes an empirical corpus of tool-to-HTTP binding failures, reproducible request witnesses, and diagnostic corrections in existing adapters. The central question is whether independently declared OpenAPI values remain independently expressible in the generated tool interface and arrive at their intended HTTP locations.

The project does **not** introduce a new alias-allocation algorithm, OpenAPI serializer, compiler, or general API-testing method. Location qualification, collision-free naming, flatten/unflatten maps, request capture, and comparison with known expected requests are established techniques. The corrections use those techniques. The original work is the selected cross-implementation evidence, its independently stated expectations and controls, and the reproducible demonstration of the corrections.

Two kinds of evidence are kept separate:

- **Interface loss:** distinct source bindings collapse into one generated property. The desired request is not representable through that interface. A recorded call uses only arguments the generated schema actually exposes.
- **Dispatch loss:** the generated schema exposes independent arguments, but the adapter drops or misroutes a value during request construction.

Multiple fixtures or omission variants of one mechanism are not counted as separate discoveries. ADK's numeric-suffix collision and FastMCP's location-suffix collision are independent implementations of the same allocation problem.

## Source revisions

| Project | Inspected and reproduced revision | Relevant implementation |
| --- | --- | --- |
| Google ADK Python | `044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5` | [Operation parser](https://github.com/google/adk-python/blob/044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5/src/google/adk/tools/openapi_tool/openapi_spec_parser/operation_parser.py), [REST tool](https://github.com/google/adk-python/blob/044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5/src/google/adk/tools/openapi_tool/openapi_spec_parser/rest_api_tool.py) |
| Prefect FastMCP | `92e44ffcc04b29f960a6c678f44fac226ccc0ea6` | [Schema and parameter mapping](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/fastmcp_slim/fastmcp/utilities/openapi/schemas.py), [request director](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/fastmcp_slim/fastmcp/utilities/openapi/director.py) |
| Open WebUI | `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d` | [Tool-schema conversion and request execution](https://github.com/open-webui/open-webui/blob/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d/backend/open_webui/utils/tools.py) |
| Keycloak API specimen | REST API **26.7.4**; corresponding source `aa9fe3fba0c6cd5770f19a49378c55f4378cf544` | [Official OpenAPI document](https://www.keycloak.org/docs-api/26.7.4/rest-api/openapi.json), [realm update implementation](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/services/src/main/java/org/keycloak/services/resources/admin/RealmAdminResource.java#L480) |

OpenAPI defines a parameter's identity using its name and location; a JSON request body has its own schema. Equal names across these locations do not require equal values. See the [OpenAPI 3.0.3 Parameter Object](https://spec.openapis.org/oas/v3.0.3.html#parameter-object).

## The closest competent baseline

FastMCP already solves ordinary parameter collisions. [PR #1107](https://github.com/PrefectHQ/fastmcp/pull/1107), closing issue #1100, established location suffixes such as `id__path` while preserving the body property's name. The more recent [issue #5112](https://github.com/PrefectHQ/fastmcp/issues/5112) and [PR #5113](https://github.com/PrefectHQ/fastmcp/pull/5113) cover generated whole-body argument names that collide with HTTP parameters.

Its pinned [whole-body collision tests](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/tests/server/providers/openapi/test_whole_body_parameter_collisions.py) use actual generated schemas, `Client.call_tool`, HTTP request capture, distinct values, and an in-process FastAPI comparison. They cover array, scalar, and dictionary bodies across path, query, header, and cookie locations. This is direct prior art for both the binding convention and the validation operation. It receives credit as a baseline, not merely as a related project.

The selected FastMCP suffix re-collision adds a narrower boundary: an original name such as `x__path` can equal a name generated for a different binding. The current allocator checks original-name overlap, then creates aliases without reserving them against every original name. This is distinct from #5113's missing whole-body name in the initial collision set. The ordinary FastMCP positive controls remain part of the evidence; the extra finding does not invalidate their successful results.

The inspected [native suffix test](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/tests/utilities/openapi/test_schemas.py#L458) does not include a source parameter already named like a generated suffix. Some older [end-to-end compatibility tests](https://github.com/PrefectHQ/fastmcp/blob/92e44ffcc04b29f960a6c678f44fac226ccc0ea6/tests/server/providers/openapi/test_end_to_end_compatibility.py#L165) only assert that a failure occurs after argument validation. Those tests should not be described as successful wire-value checks; the newer whole-body suite provides that stronger baseline.

## Nearby reports and explicit exclusions

| Existing work | Relationship to these findings |
| --- | --- |
| ADK [#6991](https://github.com/google/adk-python/issues/6991), [#6992](https://github.com/google/adk-python/pull/6992): empty composed/untyped bodies | The patch recognizes an original-name marker in the scalar/composed branch. It does not change the direct-array branch that dispatches only when the generated name is literally `array`. Our renamed-array case is adjacent, but not the same fix. |
| ADK [#4505](https://github.com/google/adk-python/pull/4505): preserve source property spelling | Preserving spelling is different from reserving generated aliases. The [existing deduplication test](https://github.com/google/adk-python/blob/044a1ec3f434cf2e3f7acfdbd52305b60d16f6e5/tests/unittests/tools/openapi_tool/openapi_spec_parser/test_operation_parser.py#L239) covers three copies of one name, not a pre-existing suffixed name. |
| Open WebUI [#29716](https://github.com/open-webui/open-webui/issues/29716), [#29717](https://github.com/open-webui/open-webui/pull/29717): path/query fields leaking into strict bodies | The fix retains a name if the body legitimately declares it. That preserves a same-value path/body call, but does not make two different values independently expressible. Our distinct-value case does not concern an undeclared body property. |
| FastMCP [#3818](https://github.com/PrefectHQ/fastmcp/pull/3818): sanitized dataclass field collisions | This is relevant prior naming work in `json_schema_to_type`, a different conversion path from the HTTP parameter map. |
| FastMCP [#4407](https://github.com/PrefectHQ/fastmcp/pull/4407): OpenAPI resource requests through RequestDirector | This addresses resource URI routing and encoding, not generated argument aliases overwriting original names. |

The corpus does not claim the already reported ADK [query style/explode](https://github.com/google/adk-python/issues/7204), [header/cookie serialization](https://github.com/google/adk-python/pull/7166), [operation parameter override](https://github.com/google/adk-python/issues/7205), [falsey query values](https://github.com/google/adk-python/issues/6287), or [truncated operation-name collision](https://github.com/google/adk-python/pull/7284) as new findings. It also excludes Open WebUI's [array-schema `items` omission](https://github.com/open-webui/open-webui/issues/14115). These are nearby but separately reported defects.

## Why the Keycloak specimen is meaningful

An ordinary Keycloak realm rename needs the current name in the URL and a new name in the body: `PUT /admin/realms/old` with `{"realm":"new"}`. This requirement is established by upstream implementation and tests, not assumed from a schema collision.

At the pinned 26.7.4 source revision, [the update implementation](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/model/storage-private/src/main/java/org/keycloak/storage/datastore/DefaultExportImportManager.java#L791) calls `renameRealm` with the representation's name. The [rename implementation](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/model/storage-private/src/main/java/org/keycloak/storage/datastore/DefaultExportImportManager.java#L735) updates the realm and related client URLs. The [native `renameRealmTest`](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/tests/base/src/test/java/org/keycloak/tests/admin/realm/RealmUpdateTest.java#L43) changes the representation while updating through the old-name resource. A [second test](https://github.com/keycloak/keycloak/blob/aa9fe3fba0c6cd5770f19a49378c55f4378cf544/tests/base/src/test/java/org/keycloak/tests/admin/realm/RealmUpdateTest.java#L96) explicitly sets `NEW`, calls `adminClient.realm(OLD).update(rep)`, and checks the renamed resources. The master realm has a separate rename prohibition; this specimen concerns an ordinary realm.

Our specimen retains the published operation, its path parameters, and components, adds an operation ID needed for tool construction, and uses a loopback server. The observer records HTTP values; it does not implement Keycloak. **No live realm was renamed, no Keycloak server was run, and these upstream Java tests were inspected rather than executed here.** The source supports the operation's semantics, while the local capture supports the adapter-binding observation.

## Evidence fidelity and limits

ADK is exercised through `OpenAPIToolset`, generated declarations, and `run_async`. FastMCP is exercised through `FastMCP.from_openapi` and its public in-process MCP client. Both send actual HTTP requests to the local observer.

Open WebUI uses a narrower component boundary: selected unchanged function bodies are loaded from the pinned source, with actual `aiohttp` and the required globals, then their conversion and request paths are exercised. This is **not** a full Open WebUI application, database, authentication, browser, or chat-session run. Diagnostic replacements are locally applied corrections, not upstream releases. Their measured scope must remain visible in reports.

The synthetic fixtures isolate binding boundaries. Keycloak supplies one real API operation, not a prevalence estimate. Selected native tests are regression controls, not complete upstream test-suite certification. The project makes no claim about model accuracy, provider compatibility, production incident rates, economic savings, security impact, or complete OpenAPI conformance.

## Search bounds

The review searched public issues and PRs, including closed results, on 27 September 2026. Targeted GitHub searches returned the following complete first pages, all below the 100-result limit:

| Repository | Queries and returned counts |
| --- | --- |
| Google ADK Python | `"array_0"`: 0; `OpenAPI collision`: 3; `OpenAPI "duplicate"`: 26; `OpenAPI "_0"`: 0 |
| Open WebUI | `OpenAPI "same name"`: 17; `OpenAPI collision`: 1; `OpenAPI "path" "body"`: 24 |
| Prefect FastMCP | `OpenAPI collision`: 22; `OpenAPI suffix`: 17; `"id__path"`: 2 |

Directly relevant issue bodies, patches, and native tests were inspected. Earlier broader searches and primary documentation complemented these queries. No exact existing report or fix was located for the selected boundaries at the inspected pins. Search indexing, phrasing, and timing limit that conclusion: **this is a non-exhaustive search, not a claim of first-ever discovery**.

Zouhair Mudakka owns the newly authored project. Research, implementation, drafting, and review used AI assistance. Upstream authors retain credit for the standards, implementations, tests, bug reports, and fixes cited here. See [third-party notices](../THIRD_PARTY_NOTICES.md).
