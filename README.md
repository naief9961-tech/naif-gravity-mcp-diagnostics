# NAIF Gravity MCP Diagnostics

A Python standard-library probe for **handshake-era MCP Streamable HTTP discovery**. Diagnose transport and protocol failures without executing server tools.

## Try it

Requires Python 3.10 or later. No packages or account required for the local examples.

```bash
git clone https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics.git
cd naif-gravity-mcp-diagnostics
python3 tools/mcp_health_check.py https://your-mcp.example/mcp
```

Use an endpoint you own or are authorized to test. For bearer authentication, provision a scoped token in your environment and pass its variable name:

```bash
python3 tools/mcp_health_check.py https://your-mcp.example/mcp --token-env MCP_TEST_TOKEN
```

## What it checks

- `initialize` → `notifications/initialized` → `tools/list` when advertised.
- Negotiated protocol and session headers, JSON-RPC response IDs and basic tool descriptors.
- JSON and SSE responses to POST requests; bounded tools pagination.
- Nonzero exits for HTTP, JSON-RPC and malformed-response failures.

The probe refuses redirects and omits tokens, session values, server bodies and tool names from output. It never sends `tools/call`, executes a repair, or purchases a service.

Supported revisions: **2025-03-26, 2025-06-18, 2025-11-25**. This is not a full conformance suite and does not implement OAuth login, stdio, legacy SSE transport or newer stateless lifecycle revisions. Read the [quick start and limits](docs/DIAGNOSTIC-QUICKSTART.md).

## See a healthy and a broken MCP response

Run a self-contained demonstration from the complete checkout (Python standard library only):

```bash
python3 examples/mcp_discovery_demo.py
```

It starts temporary loopback fixtures and uses the actual probe. Healthy discovery exits `0`; a response with HTTP `200` but the wrong JSON-RPC request ID exits `1`. The demo itself exits `0` only when both expected results occur. No credentials, external endpoints or tool execution are involved.

```text
Scenario: json
[initialize] HTTP 200
protocol: 2025-11-25
session: present
[notifications/initialized] HTTP 202
[tools/list] HTTP 200
tools: 1
PASS: bounded discovery completed. No tools were executed.
probe exit: 0
requests: initialize -> notifications/initialized -> tools/list

Scenario: wrong-id
[initialize] HTTP 200
FAIL: mismatched request ID or invalid response shape
probe exit: 1
requests: initialize
```

This demo reuses the synthetic fixtures in `tests/test_mcp_health_check.py`; keep the full checkout. It demonstrates two cases, not full MCP conformance.

## Run a reproducible example locally

```bash
python3 examples/webhook_signature_fixture.py
python3 -m unittest discover -s tests -p test_mcp_health_check.py -v
```

The synthetic webhook example demonstrates why parsing and reserializing JSON can break raw-body HMAC verification. It is not a provider-specific verifier. Tests run against loopback fixtures and cover sessions, JSON/SSE, auth, pagination, redirects and failures.

## JSON for agents and GitHub Actions

```bash
python3 tools/mcp_health_check.py https://your-authorized-mcp.example/mcp --json
python3 examples/json_report_demo.py
```

`--json` emits one sanitized report with pass/fail status, protocol revision, HTTP observations, complete tool count and structured failure details. Exit `0` indicates completed bounded discovery; exit `1` indicates failure. CLI syntax errors retain argparse exit `2` behavior. It omits URLs, credentials, session values, server bodies and tool names.

The included GitHub Actions workflow runs manually with local fixtures by default. Remote probing requires an explicit manual choice and a configured authorized endpoint. See the [agent and CI guide](docs/AGENT-AND-CI.md) for the JSON contract, examples and setup.

## Fault lab and issue drafts

Reproduce seven healthy and intentionally broken discovery cases locally, then turn a probe JSON report into a Markdown issue draft:

```bash
python3 examples/fault_lab.py
python3 examples/fault_lab.py --case wrong-id --report > probe-report.json
# Expected exit 1 for this intentional fault; continue with:
python3 tools/issue_report.py probe-report.json > issue-draft.md
```

The lab uses temporary loopback fixtures only. The draft generator selects bounded diagnostic fields, ignores server messages and arbitrary metadata, and never submits an issue. Add your synthetic reproduction and environment details, then review before sharing. See the [fault lab and issue guide](docs/FAULT-LAB-AND-ISSUES.md) for cases, exit semantics and stdin usage.

## Compare discovery before and after an update

```bash
python3 tools/integration_guard.py before.json after.json --json
python3 examples/integration_guard_demo.py
```

The offline guard compares a healthy baseline with a current probe report. Failed discovery, lost tool capability or decreased tool count exits 1. Other healthy changes are reported for review; `--strict-changes` also blocks them. Invalid or incomparable input exits 2. Keep the same endpoint, auth scope and requested revision. Tool names/schemas are omitted from reports, so equal-count tool substitutions are not detectable. See the [integration guard guide](docs/INTEGRATION-GUARD.md) for policy and CI usage.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md). Report a minimal synthetic reproduction, expected behavior, Python version and negotiated MCP revision. **Issues are public: never attach credentials or production/customer data.**

## Project context

These diagnostic files were developed in [NAIF Gravity's Diagnostic Hub](https://github.com/naief9961-tech/ai-growth-engine/blob/main/NAIF-GRAVITY.md) and extracted into this standalone repository. See [NOTICE.md](NOTICE.md) for provenance. No code or workflows from the original AI Growth Engine project are included.

The optional hosted service is at [naifgravity.com](https://naifgravity.com). This repository can be used independently of it.

If the diagnostics help you, consider starring this repository so you can find it again.

## License

MIT; see [LICENSE](LICENSE). Applies to this diagnostic utility and documentation, not to the hosted service.
