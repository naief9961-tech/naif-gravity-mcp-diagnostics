# Offline MCP integration guard

Compare a known healthy probe result with a result captured after a change. Python 3.10+, standard library only. The guard reads two local JSON files; it does not send network requests, execute tools, deploy, roll back or modify either report.

## Capture comparable reports

Use the **same endpoint, requested revision, authorization scope and probe commit** before and after your server/configuration update. Only probe endpoints you own or are authorized to test.

```bash
python3 tools/mcp_health_check.py https://your-authorized-mcp.example/mcp --json > before.json
# Only keep a completed successful discovery as the baseline.
# After your authorized update, capture the same configuration again:
python3 tools/mcp_health_check.py https://your-authorized-mcp.example/mcp --json > after.json
# Failed probes exit 1 but still produce JSON. Then run:
python3 tools/integration_guard.py before.json after.json
python3 tools/integration_guard.py before.json after.json --json
```

For auth, use the same scoped token environment variable with `--token-env MCP_TEST_TOKEN`. Never embed its value in a command or report.

## Policy and exit codes

| Observation | Default exit | Meaning |
| --- | --- | --- |
| No observed change | 0 | Bounded observations are unchanged |
| Healthy discovery with increased tool count, changed revision, session presence or HTTP trace | 0 | Change reported for review |
| Discovery fails after healthy baseline | 1 | Regression observed; investigate configuration/client/server |
| Tool capability disappears or complete tool count decreases | 1 | Potential breaking change; intentional removals need review |
| Invalid input, unhealthy baseline, different requested revisions | 2 | Inconclusive; cannot establish this comparison |

`--strict-changes` also exits 1 for any healthy observed change. This policy is deliberately conservative: a protocol revision or session change is not automatically a failure. Review intentional changes and explicitly recapture a healthy baseline after approval; the guard never replaces the baseline itself.

Input is limited to 1 MiB per report, schema 1.0, bounded discovery request observations and consistent statuses. The JSON output contains only fixed status/reason codes and change labels. It does not copy input paths, endpoints, tokens, session values, arbitrary metadata or error messages. CLI argument errors keep argparse exit 2 behavior.

## Important measurement limits

Reports omit endpoint identity and tool names/schemas. The guard cannot verify that the two files describe the same endpoint or token scope. The operator must keep those settings consistent. A tool rename, substitution or schema change with unchanged count is **not detectable**. It cannot prove full compatibility, validate tool execution, payment flows, OAuth renewal or webhook delivery. Transient failures or deliberate tool removals can trigger a regression observation; no automatic repair occurs.

## Local demonstration

```bash
python3 examples/integration_guard_demo.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The demo captures healthy and broken loopback discovery reports, then demonstrates a tool-count increase by editing a synthetic report in memory. It exits 0 only when expected guard outcomes occur.

## CI use

Once your own authorized job produces comparable files, add:

```bash
python3 tools/integration_guard.py before.json after.json --json
# Optional: block every observed change for manual review:
python3 tools/integration_guard.py before.json after.json --strict-changes --json
```

Preserve and inspect exit 1 and exit 2; never use `|| true` to treat an inconclusive comparison as success. Keep baseline capture explicit. The repository's manual workflow validates synthetic examples only by default and does not capture a production baseline.
