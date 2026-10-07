# Machine-readable diagnostics and manual CI

## JSON contract

```bash
python3 tools/mcp_health_check.py https://your-authorized-mcp.example/mcp --json
```

After valid CLI arguments, stdout contains one JSON document; exit `0` means bounded discovery completed, `1` means configuration, discovery or interruption failure. Argument parsing/help retains normal argparse behavior (invalid syntax exits `2` on stderr); callers must handle that separately.

Report schema version `1.0` contains:

| Field | Meaning |
| --- | --- |
| `status`, `exit_code` | `pass`/`fail` and the process exit code |
| `requested_protocol_version` | Requested supported revision |
| `negotiated_protocol_version` | Validated server revision, otherwise null |
| `session_present` | Boolean or null before a probe is created; never the session value |
| `tools_advertised` | Boolean or null before capabilities are validated |
| `tool_count` | Count only after complete tools discovery; null when absent or incomplete |
| `tools_executed` | Always false for this utility |
| `requests` | Completed HTTP response observations: method and status; not proof of protocol success |
| `error` | Null on success, otherwise code, method and sanitized message |

Error codes are `configuration_error`, `discovery_failed` and `interrupted`. Agents should branch on codes and exit status, not message wording. An HTTP 200 observation can still produce a failed report. Network failures can leave no response observation; `error.method` identifies the attempted method. Endpoint URLs, tokens, session values, tool names, server bodies and server error messages are omitted. This is discovery, not proof that a tool executes correctly or a full conformance check.

Try without external services or credentials:

```bash
python3 examples/json_report_demo.py
python3 examples/json_report_demo.py --failure  # intentionally exits 1
```

Keep the complete checkout: these demonstrations reuse the tested synthetic fixtures.

## GitHub Actions

The repository includes `.github/workflows/mcp-diagnostics.yml`. It uses `workflow_dispatch` only: no schedule, push trigger, deployment or automatic live probe. The default manual run executes loopback tests and examples, and prints a validated local JSON report.

To use it in another repository, copy the diagnostic tool, tests and examples with the workflow, or first check out a reviewed version of this repository. The workflow uses the official `actions/checkout@v7` action with read-only contents permissions and credential persistence disabled. For reproducible supply-chain control, pin the action to a reviewed full commit SHA in your own workflow.

For an optional live check:

1. Configure repository variable `MCP_DIAGNOSTIC_URL` with an endpoint you own or are authorized to test. Do not embed credentials in its URL.
2. If required, configure repository secret `MCP_DIAGNOSTIC_TOKEN` with a scoped bearer token. Do not put it in a variable, workflow file or command argument.
3. Run the workflow manually and explicitly select `run_remote`. Leave it false for local examples only.

The remote step prints only the sanitized JSON report, preserves probe failures as job failures, and uses a five-second per-request timeout within a five-minute job limit. Repository variables are for nonsecret values; do not place private endpoint information there. The workflow does not upload artifacts. Normal GitHub Actions quotas/billing apply in the repository where it is used; no paid plan is required by this example.

Do not give live secrets to untrusted pull request code, use `pull_request_target` to execute it, or enable automatic repairs/payments. This workflow sends discovery requests only and uses the same supported protocol revisions and limits as the CLI.
