# Fault lab and local issue drafts

Requires Python 3.10+ and the complete checkout. No dependencies, accounts or secrets are needed. The lab reuses existing synthetic fixtures and the actual discovery probe. Servers bind temporarily to loopback only.

```bash
python3 examples/fault_lab.py
python3 examples/fault_lab.py --case wrong-id
python3 examples/fault_lab.py --json
```

| Case | Expected probe exit | Next check |
| --- | --- | --- |
| healthy | 0 | Valid discovery control |
| missing-token | 1 | HTTP 401; scoped token and auth configuration |
| wrong-id | 1 | HTTP 200 with mismatched RPC ID; response correlation |
| invalid-json | 1 | HTTP 200 with invalid JSON; routing and serialization |
| unsupported-version | 1 | Client/server supported revision overlap |
| cursor-loop | 1 | Pagination progress and terminal page |
| invalid-tool-schema | 1 | Object input schema and descriptor validation |

The default lab and `--json` exit **0 when expected outcomes are reproduced**, including intentional failures. This verifies the demonstration, not a real endpoint. The JSON lab document contains individual probe reports. This is a small teaching lab, not full conformance, an expired-token simulator or an OAuth implementation. An unsupported revision may be a probe limitation rather than a server defect.

With one case, `--report` emits only probe JSON and preserves its exit code:

```bash
python3 examples/fault_lab.py --case wrong-id --report > probe-report.json
# Expected exit 1: the intentionally broken server was detected.
python3 tools/issue_report.py probe-report.json > issue-draft.md
```

The separate raw-body webhook HMAC example remains available:

```bash
python3 examples/webhook_signature_fixture.py
```

## Draft from your own authorized probe

```bash
python3 tools/mcp_health_check.py https://your-authorized-mcp.example/mcp --json > probe-report.json
# A failed probe exits 1 but still writes its JSON report.
python3 tools/issue_report.py probe-report.json > issue-draft.md
# Alternatively, read one probe report from stdin:
python3 tools/issue_report.py < probe-report.json
```

The generator writes Markdown to stdout and never contacts GitHub or submits an issue. Draft generation exits 0 on successful conversion, even for a failed probe. Invalid, oversized or non-probe input exits 2 with a generic error. With shell pipelines, enable `set -o pipefail` to preserve the original failing probe status.

Only known status, revision, method and numeric observations are included. Arbitrary metadata, URLs and even `error.message` are ignored. Unknown revisions are rendered as an unknown/unsupported label. No raw server messages, bodies, session values, tool names or credentials are copied. This is field selection, not a general-purpose sanitizer for arbitrary logs.

Before sharing, add a minimal synthetic reproduction, exact probe commit, Python/OS version and server implementation/version. Review anything you add manually. A failure is an observation and may reflect configuration or a client limitation. Check existing issues and share only relevant reports; never post credentials or repeat unsolicited reports.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 examples/fault_lab.py
```
