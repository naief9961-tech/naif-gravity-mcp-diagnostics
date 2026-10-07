# Diagnostic quick start

Gather a small, reproducible integration failure before opening a public issue. The MCP probe uses Python 3's standard library and makes discovery requests only.

## MCP: Streamable HTTP discovery

```bash
git clone https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics.git
cd naif-gravity-mcp-diagnostics
python3 tools/mcp_health_check.py https://your-mcp.example/mcp
```

Replace the example hostname with an endpoint you own or are authorized to test. Default requested revision: `2025-06-18`. `--protocol-version` also accepts `2025-03-26` and `2025-11-25`. These are supported **handshake-era** revisions, not every MCP revision.

The probe negotiates `initialize`, sends `notifications/initialized`, and forwards the negotiated `MCP-Protocol-Version` and any `Mcp-Session-Id` on subsequent requests. If tools are advertised, it reads `tools/list` pages. It parses plain JSON or SSE responses to POST requests. It never calls a tool.

### Bearer authentication

Provision a scoped test token in your environment through your normal secret manager or secure local session. Specify the variable name, not the token:

```bash
python3 tools/mcp_health_check.py https://your-mcp.example/mcp --token-env MCP_TEST_TOKEN
```

Tokens are not printed or saved by the probe. Authentication requires HTTPS except on loopback. Redirects are refused, preventing authorization from being forwarded to a new destination. Do not put credentials in the endpoint URL or paste tokens in GitHub issues. No OAuth login or refresh flow is implemented.

### Illustrative output

Protocol and count depend on the server:

```text
[initialize] HTTP 200
protocol: 2025-06-18
session: present
[notifications/initialized] HTTP 202
[tools/list] HTTP 200
tools: 3
PASS: bounded discovery completed. No tools were executed.
```

Exit status: `0` after supported discovery completes, `1` for a probe failure, `2` for invalid CLI arguments. A valid server without a tools capability can also succeed. Response bodies, server error messages, tool names, session values, and tokens are omitted from output.

| Finding | Next check |
| --- | --- |
| HTTP 401 | Test token, scheme, expiry, issuer and audience |
| HTTP 403 | Scope, role, resource ownership and policy |
| JSON-RPC error | Protocol/method compatibility; inspect detailed error locally |
| Invalid response ID or shape | Request IDs and JSON-RPC structure |
| SSE ends before matching response | Proxy buffering, disconnect, server logs |
| Unsupported revision | A client supporting the negotiated revision |

### Bounds and limitations

- Default socket timeout: 10 seconds; `--timeout` accepts up to 60 seconds. This is a connect/read inactivity timeout, not a strict wall-clock deadline. SSE checks elapsed time between line reads.
- Response/stream limit: 1 MiB per request. SSE line limit: 64 KiB. Maximum tools/list pages: 10; repeated cursors fail.
- No stdio, legacy separate GET/SSE + POST transport, SSE reconnection, server-initiated RPC requests, OAuth login, or stateless post-2025 lifecycle support.
- Basic envelope and tool-descriptor checks are not full JSON Schema or MCP conformance validation. A PASS establishes discovery, not execution, repair quality, or production health.
- No session-termination DELETE request is sent; servers may expire the short-lived session normally.

Protocol references: [2025-06-18 lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle) and [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).

## API / Auth evidence

Include method, sanitized route, status, auth scheme, sanitized error code, expected behavior, and a minimal reproduction. Never copy live Authorization headers or token-bearing URLs.

Fictional example:

```text
Method: GET
Route: /v1/example-resource
HTTP status: 403
Authentication scheme: Bearer (token omitted)
Expected: read a resource owned by the test account
Observed: insufficient_scope
Reproduction: use a test account with the documented read scope
```

Include only synthetic or redacted reproduction data in an issue.

## Webhook evidence

Record provider, sanitized event type, delivery and handler statuses, signature result, and redacted payload shape. Check raw-body bytes and idempotency separately. Successful delivery does not establish successful application processing.

Try the [offline signature fixture](../examples/webhook_signature_fixture.py), include the smallest synthetic reproduction in an issue.

## Local verification

```bash
python3 -m unittest discover -s tests -p test_mcp_health_check.py -v
python3 examples/webhook_signature_fixture.py
```

Tests use loopback fixtures only. The webhook example uses synthetic data and a fictional key; it makes no network requests and is not a provider-specific verifier.

## Share sanitized evidence only

GitHub issues are public. Remove credentials, cookies, signing secrets, private keys, payment details, customer data, and private endpoint information. Prefer synthetic fixtures.

Return to the [Diagnostic Hub](https://github.com/naief9961-tech/ai-growth-engine/blob/main/NAIF-GRAVITY.md).
