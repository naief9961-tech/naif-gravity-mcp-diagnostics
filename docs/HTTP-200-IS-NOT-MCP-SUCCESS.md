# HTTP 200 is not enough: checking MCP discovery without executing tools

An MCP endpoint can return HTTP 200 while the integration still fails. A successful HTTP request does not establish that the response matches the JSON-RPC request, that initialization negotiated a supported revision, or that subsequent requests carry the session headers.

NAIF Gravity MCP Diagnostics is a small Python standard-library probe for that narrower question: can a client complete supported Streamable HTTP discovery?

Repository: https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics

## The sequence matters

For the handshake-era revisions supported by this probe, discovery follows this sequence:

1. Send `initialize` and validate the response ID, result shape and negotiated revision.
2. Forward the negotiated `MCP-Protocol-Version` and any returned `Mcp-Session-Id`.
3. Send `notifications/initialized` without a request ID.
4. If the server advertises tools, request `tools/list` and follow bounded pagination.

A JSON-RPC error inside an HTTP 200 response is still a failure. A mismatched response ID is also a failure: it cannot establish that the reply belongs to this request.

## Try it on an endpoint you may test

Requires Python 3.10 or later; no third-party packages.

```bash
git clone https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics.git
cd naif-gravity-mcp-diagnostics
python3 tools/mcp_health_check.py https://your-mcp.example/mcp
```

Replace the example endpoint with one you own or are authorized to test. For bearer authentication, provision a scoped test token securely in your environment and pass only its variable name:

```bash
python3 tools/mcp_health_check.py https://your-mcp.example/mcp --token-env MCP_TEST_TOKEN
```

This does not perform OAuth login or refresh. Bearer authentication requires HTTPS except on loopback, and redirects are refused.

## JSON and SSE are both valid response shapes

A POST response may contain JSON or an SSE stream. The probe reads SSE comments and multiline data, ignores unrelated notifications, and stops when it receives the matching response. It does not require the stream to close first.

Output includes HTTP statuses, protocol revision, whether a session exists, and tool count. It omits response bodies, tool names, session values and bearer tokens. Failures return a nonzero exit status.

## Reproduce behavior without production access

```bash
python3 -m unittest discover -s tests -p test_mcp_health_check.py -v
python3 examples/webhook_signature_fixture.py
```

The 11 test methods use loopback fixtures covering sessions, authentication, JSON/SSE, pagination, redirect refusal and malformed responses. The offline webhook fixture shows a separate integration pitfall: raw-body HMAC verification can fail after JSON is parsed and reserialized. Its key and payload are fictional.

## Know what PASS means

Supported revisions are 2025-03-26, 2025-06-18 and 2025-11-25. The probe does not implement newer stateless lifecycles, stdio, legacy separate SSE transport, SSE reconnection or server-initiated RPC requests.

Requests are bounded to 1 MiB each and tools discovery to 10 pages. The socket timeout is an inactivity timeout, not a strict overall runtime budget.

PASS means supported discovery completed. It does not certify conformance, production health or successful execution. The probe never calls a server tool.

The repository includes a [quick start with limits](https://github.com/naief9961-tech/naif-gravity-mcp-diagnostics/blob/main/docs/DIAGNOSTIC-QUICKSTART.md). Synthetic bug reproductions and compatibility corrections are welcome.

Disclosure: this utility belongs to the NAIF Gravity project. The article was prepared with AI assistance and checked against the implementation and local tests.
