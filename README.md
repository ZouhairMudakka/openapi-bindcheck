# openapi-bindcheck

**Does a schema-valid tool call put each value in the intended HTTP location?**

This repository contains reproducible OpenAPI-to-tool binding findings, a small wire-request oracle, and controlled diagnostic corrections. It exercises pinned Google ADK and FastMCP packages through their actual tool entry points, plus an explicitly bounded Open WebUI component reproduction. No model, API key, or external business service is needed.

Maintained by **Zouhair Mudakka**. Original investigation, fixtures, harness, and documentation were developed with AI assistance. Upstream implementations and established techniques are attributed in [prior work](docs/PRIOR_ART.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## The contribution

Tool-schema validity alone does not establish request fidelity. We found and reproduced:

- **ADK: a renamed array-body argument is accepted, then omitted from HTTP.** A declared query parameter named `array` changes the body argument to `array_0`; dispatch still looks for `array`. Even omitting that optional query value can lose the supplied body.
- **ADK and FastMCP: a generated alias can steal another original name.** ADK's `x_0` and FastMCP's `x__path` can collide with an independently declared parameter. The generated interface then cannot represent every source value independently.
- **Open WebUI's tested components: path and body names are flattened together.** The interface cannot express a different path `realm` and body `realm`. A source-derived Keycloak realm-rename operation supplies a concrete API contract where those values need to differ.

The contribution is the **specific empirical findings, location-qualified corpus, wire witnesses, and discriminating corrections/ablations**. Request capture, separate parameter locations, and collision-free name allocation are established techniques. We do not claim a new allocation algorithm, universal novelty, or a complete OpenAPI implementation. Prior-art searches preceded the experiments; their scope and closely related existing fixes are documented in [PRIOR_ART.md](docs/PRIOR_ART.md).

## Measured result

| Bounded comparison | Original | Diagnostic correction |
|---|---:|---:|
| ADK, eight-case ablation corpus | 3/8 | Body-only 6/8; alias-only 4/8; both **8/8** |
| FastMCP, four-case additional alias corpus | 2/4 | **4/4** |
| Unchanged selected ADK native tests | 131/131 | **131/131** |
| Unchanged selected FastMCP native tests | 25/25 | **25/25** |

The primary comparative run also contains four passing FastMCP baselines, four passing ADK cases and three ADK failures, and two passing/two failing Open WebUI component cases. Some cases appear again in the ablation corpus: **do not add these counts as independent defects or interpret them as framework rankings**. There are three failure families here; the alias family occurs in two implementations.

Six parameter-order controls and one retained path-rejection control check the ADK corrections separately. The oracle tests reject corrupted request facts, forged saved pass flags, extra/missing requests, and JSON type mismatches. A separate verifier check rejects 17 altered-report variants, including coordinated changes to a captured request and its saved expectation.

All results concern the exact source pins in [sources.json](experiments/sources.json), captured on 2026-09-27. They do not imply that a later release still has these behaviors. [Recorded evidence](results/reference/) includes schemas, supplied arguments, intended bindings, observed requests, source hashes, and the recomputed summary.

## Quick inspection (standard library only)

Requires Python 3.12 or later for the small checker; full reproduction is validated on Python 3.12.

```sh
python -m pip install .
openapi-bindcheck results/reference/adk-ablation-original.json results/reference/adk-ablation-both.json
openapi-bindcheck --require-all results/reference/adk-ablation-both.json results/reference/fastmcp-suffix-corrected.json
python -m unittest discover -s tests -v
```

Original defect witnesses deliberately fail fidelity checks. The command exits nonzero for them only with `--require-all`. The checker recomputes results from requests; it does not trust recorded `pass` fields. Expectations remain part of the input contract, so use independently authored ones. The full experiment verifier additionally fixes case IDs, contracts, and expected failure signatures in code.

For your own adapter, capture a request and describe the intended source values:

```python
from openapi_bindcheck import check_request

failures = check_request(
    {"method": "PUT", "path": "/admin/realms/old",
     "query": {}, "body": {"realm": "new"}, "absent_headers": ["x-debug"]},
    captured_request,  # {method, path, query, body, headers}
)
assert not failures, failures
```

Query values use lists, as returned by `urllib.parse.parse_qs`. Body comparison is parsed, structural JSON equality with exact Python types (`1`, `1.0`, and `True` are distinct). Requested headers are compared case-insensitively by name; unrelated transport headers are ignored. This small oracle has no automatic adapter discovery or general schema-to-fixture generator.

## Reproduce from source

Use a disposable **Python 3.12** virtual environment. Setup downloads public pinned sources and dependencies. Runs then use only loopback HTTP. Allocate normal development disk space for two source archives, a virtual environment, and reports.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python experiments/setup.py
python experiments/reproduce.py --native
```

On Windows PowerShell, create the venv with Python 3.12 and use its interpreter directly:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe experiments/setup.py
.\.venv\Scripts\python.exe experiments/reproduce.py --native
```

Reports go to `results/local/`; downloaded sources to `.cache/`. `BINDCHECK_RESULTS` and `BINDCHECK_CACHE` override those directories. Every repair mode runs in a fresh interpreter. The pipeline fails on changed source hashes, unexpected case coverage, schema/runtime errors, wrong failure signatures, or incomplete native suites. GitHub Actions performs a fresh installation and reproduction on Linux and Windows.

The experiment lock records the runtime/test dependencies used by these specific seams, installed with `--no-deps`; this is a deliberately bounded test environment, not an installation recipe for every SDK feature. Source packages are installed from commit-pinned archives. Build backends and package-index artifacts are not fully hermetically locked. FastMCP's source archive reports version `0.0.0` because its version normally comes from Git; we identify it by its commit and all 258 Python source-file hashes, not that version string. ADK's 765 Python source files are also checked against its pinned tree.

Archive extraction omits unused upstream symlinks (maintainer documentation links); package source and selected test files retain their original bytes. Published reference JSON normalizes ephemeral loopback ports to `0`; its manifest records both raw and normalized hashes. Request values are otherwise preserved.

## Boundaries and use

**For developers:** these fixtures can catch silent argument loss when changing tool generators or dispatch code. The advantage demonstrated here is preservation of independently intended values, with unchanged selected native tests. We have not measured production frequency, adoption, saved debugging time, model accuracy, or revenue. The most immediate practical value is a reusable regression corpus and precise upstream-quality reproductions.

**Execution fidelity:** ADK uses the real `OpenAPIToolset`/tool execution path; FastMCP uses `from_openapi` plus `Client.list_tools/call_tool`. ADK parser metadata is inspected to discover generated aliases. Open WebUI compiles three unchanged function ASTs from its pinned source with real aiohttp and a local HTTP observer; it does **not** initialize the full app, database, chat, or authentication stack. No Open WebUI correction is claimed.

**Expressibility matters:** alias and flattened-name failures cannot encode all distinct intended values in the generated interface. Their supplied calls are explicitly labeled lossy diagnostic projections. Only the ADK array-body finding demonstrates a faithfully supplied, representable body value disappearing during dispatch.

**Keycloak is a schema specimen:** its own source and native test demonstrate the old-path/new-body rename contract. This experiment extracts that PUT operation and components, adds an `operationId`, and substitutes a loopback server. It does not run Keycloak or perform a realm rename.

**Diagnostic corrections:** the conventional fixes are applied in memory to exact pinned source, with hash and replacement-shape guards. They are not production middleware or supported upstream patches. General OpenAPI serialization, authentication, every content type, all framework tests, and model-provider schema compatibility remain outside scope.

The authored core and harness are MIT-licensed. Downloaded upstream projects and in-memory derived code retain their own terms; Open WebUI's custom license is not relabeled MIT. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
