<p><img src="assets/naif-gravity-mark.svg" alt="NAIF Gravity" width="128" height="128"></p>

# NAIF Gravity MCP Diagnostics

<!-- naif-storefront-refresh-20261030 -->
## New look at NAIF Gravity — 30 October 2026

The NAIF Gravity storefront has a refreshed visual identity: midnight navy, copper accents and a glass-inspired homepage experience, with Arabic and English controls. Explore the updated [storefront](https://naifgravity.com) and [service catalog](https://naifgravity.com/services).

**مظهر جديد لمتجر NAIF Gravity:** هوية كحلية ونحاسية وتجربة زجاجية في الصفحة الرئيسية، مع خيارات العربية والإنجليزية. [شاهد المتجر](https://naifgravity.com).

This announcement covers the storefront design. Service scope, availability and current prices are stated on the relevant live service pages; the redesign does not establish new product readiness.
<!-- /naif-storefront-refresh-20261030 -->

[![M8ven Verified](https://m8ven.ai/badge/mcp/naief9961-tech-naif-gravity-mcp-diagnostics-srt2tw?v=897b35b265319b33b7514ba3371e0f6a&variant=verified)](https://m8ven.ai/mcp/naief9961-tech-naif-gravity-mcp-diagnostics-srt2tw?s=readme)

A Python standard-library probe for **handshake-era MCP Streamable HTTP discovery**. Diagnose transport and protocol failures without executing server tools.

**Related field reports:** [NAIF Gravity's GitHub Issue Radar — MCP compatibility and x402 header failures (14 Oct 2026)](https://github.com/naief9961-tech/ai-growth-engine/blob/main/docs/GITHUB-ISSUE-RADAR-2026-10-14.md) offers source-linked repair plans. These are external issue analyses, not patches implemented by this probe; this tool does **not** handle stdio.

## Match the failing boundary first

A successful HTTP status does not prove that an MCP tool or downstream workflow worked. Use the smallest *local* check that matches the observed failure before asking an agent to invoke any remote service.

| What the developer sees | First free check | What this repository can establish |
| --- | --- | --- |
| `MCP initialize` times out, a Streamable HTTP handshake fails, or `tools/list` is missing | Run the [bounded Python MCP discovery probe](docs/DIAGNOSTIC-QUICKSTART.md) on an endpoint you own or have authorization to test | Initialize/session/tools-list evidence only; no `tools/call` |
| A tool's input schema is rejected after discovery | Compare the advertised descriptor with a minimal synthetic argument and the client's supported schema features | The probe collects bounded tool descriptors; it does not fully validate client-specific schema dialects |
| n8n webhook returns `200`, but the next node reads `undefined` from `body` | See the [field-path troubleshooting guide](https://naifgravity.com/discover/n8n-webhook-field-mapping) and test with synthetic fixtures | Mapping fault; **not** fixed by the MCP discovery probe |
| Webhook HMAC signature mismatch or duplicate delivery after retry | Compare raw signed bytes, timestamp and replay policy using the [webhook signature guide](https://naifgravity.com/discover/webhook-signature-mismatch) | Signature/retry fault; not a field-mapping purchase |
| JSON trailing comma or parse failure | Use a local JSON parser and the [syntax guide](https://naifgravity.com/discover/json-trailing-comma) | A parse result is not complete schema validation |

For compatible coding agents, the [free-first emergency-triage Skill](skills/naif-agent-emergency-triage/SKILL.md) describes when to use each diagnostic and when to **stop without buying anything**. A paid service is optional, separately scoped and requires the buyer's explicit authorization; current eligibility and pricing are defined only by [the live catalog](https://naifgravity.com/api/agent/catalog).

## NAIF SUPERNOVA — package distribution

The existing free NAIF Error Passport now has **source packaging** for
`naif-gravity-mcp-doctor` on PyPI and npm. The Node package is a thin,
offline-by-default launcher and **requires Python 3.10+**.
Check registry pages before installing: **a GitHub release does not prove
either package is published**. No account credentials or installer telemetry
are needed to build locally. See the
[packaging and trusted-publisher guide](docs/PACKAGE-DISTRIBUTION.md).

## NAIF Error Passport — local evidence card (free alpha)

**Current public release:** [v0.2.1 — NAIF Error Passport](https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics/releases/tag/v0.2.1). Version v0.2.1 corrects the portable Action metadata description limit; the free local diagnostic behavior is unchanged. The official Skills CLI can discover this repository's Skill without installing it: `DISABLE_TELEMETRY=1 npx skills add naief9961-tech/naif-gravity-mcp-diagnostics --list`.

The existing MCP diagnostic probe now has an **opt-in, local Error Passport**. It turns a sanitized discovery report into a small fingerprinted evidence card with free next steps. A healthy result never recommends a paid service; a failed result is a diagnosis, **not** a completed repair. No external logging, payment, tool execution or customer data upload.

Run from the checked-out repository:

    python3 tools/error_passport.py --probe https://your-authorized-mcp.example/mcp --authorized
    # Offline from an existing sanitized report (no network):
    python3 tools/error_passport.py --report sanitized-report.json --format markdown

Only use an endpoint you own or are authorized to test. The command requires Python 3.10+ and no extra packages. It is **not yet published to npm or PyPI**. Read the [Error Passport CLI/CI guide](docs/ERROR-PASSPORT.md) and use the [optional offline GitHub Action](.github/actions/error-passport/action.yml) to display a sanitized passport in manual CI summaries. Remote probing is never automatic.

### Install the free troubleshooting Skill in a coding agent

The Skill is already in this public repository. Developers using the [skills.sh CLI](https://www.skills.sh/docs/cli) can choose to install the instructions for their own agent:

    npx skills add naief9961-tech/naif-gravity-mcp-diagnostics --skill naif-agent-emergency-triage

This installs the **Skill instructions**; it does not automatically install the separate Python CLI or run a probe. For the working CLI, clone this repository and use the Error Passport commands above. The current skills CLI requires a supported Node.js version and may collect anonymous installation telemetry unless disabled; consult its documentation before opting in. No installer or buyer contacts are initiated by this README.

For reusable workflows in other GitHub repositories, the [root Error Passport action](action.yml) accepts an existing sanitized JSON report. See the [portable-action instructions](docs/ERROR-PASSPORT.md); it does not probe endpoints automatically and has a separate GitHub Marketplace publication status; **publishing a repository release alone does not prove Marketplace listing**. Check the live Marketplace listing independently.

**Optional free chat explanation:** After generating a sanitized [Error Passport](docs/ERROR-PASSPORT.md) locally, you may ask **`@naif-json-api-tools`** on [ASI:One](https://asi1.ai/) to explain its MCP discovery category. The chat never runs the probe, executes tools, repairs servers or pays for anything. Keep credentials and private evidence out of chat; the local guide works independently and remains the default.

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

## Optional NAIF Gravity commercial services — October 2026

This standalone MCP diagnostic probe is **free**, with no purchase or commercial dependency. When a verified technical repair or structured-data service is needed beyond these free diagnostics, see the [current NAIF Gravity service pages](https://naifgravity.com/services) and the [live agent catalog](https://naifgravity.com/api/agent/catalog).

**The October launch promotion has ended.** Its deadline was no later than 26 October 2026 at 05:40 UTC. Consult the live service pages and accepted quote for current prices; existing accepted quotes retain their agreed terms. Checkout does **not** imply instant autonomous implementation; most engineering products require a separate verified paid Work fulfillment.

Separate instant-per-call x402 endpoints, methods and live prices are available through the [machine-readable x402 manifest](https://naifgravity.com/.well-known/x402) and the [x402 catalog](https://naifgravity.com/api/x402/catalog). The existing four full-scope x402 products remain $1, $2, $3 and $5 USDC per call. Proposed lower-priced Lite tools are not available for purchase yet. The wallet path follows the store's regional payment policy (Saudi-classified clients use the non-wallet checkout). Do not send private keys, credentials or customer records in diagnostics.

## Project context

These diagnostic files were developed in [NAIF Gravity's Diagnostic Hub](https://github.com/naief9961-tech/ai-growth-engine/blob/main/NAIF-GRAVITY.md) and extracted into this standalone repository. See [NOTICE.md](NOTICE.md) for provenance. No code or workflows from the original AI Growth Engine project are included.

The optional hosted service is at [naifgravity.com](https://naifgravity.com). This repository can be used independently of it.

If the diagnostics help you, consider starring this repository so you can find it again.

## License

MIT; see [LICENSE](LICENSE). Applies to this diagnostic utility and documentation, not to the hosted service.
