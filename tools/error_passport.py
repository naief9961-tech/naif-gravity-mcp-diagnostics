#!/usr/bin/env python3
"""NAIF Error Passport: local, free-first MCP discovery evidence card.

Consumes a sanitized NAIF MCP probe JSON report, or explicitly runs the
existing bounded probe on an endpoint the operator is authorized to test.
No tool execution, payment, telemetry, file uploads or changes to the target.
Python 3.10+ standard library only.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

# Works both as the original standalone script and as an installed Python package.
if __package__:
    from .issue_report import render as validate_probe_report
else:
    from issue_report import render as validate_probe_report

MAX_INPUT = 32768
PROTOCOLS = {'2025-03-26', '2025-06-18', '2025-11-25'}
DIAGNOSTIC_GUIDE = 'https://naifgravity.com/discover/mcp-server-not-responding'
OPTIONAL_SERVICE = 'https://naifgravity.com/service/mcp-tool-mini'
DEFAULT_STEPS = [
    'Reproduce the fault using a minimal synthetic example.',
    'Inspect logs on the server you control; keep secrets and customer data local.',
    'Check the free MCP troubleshooting guide before considering paid help.',
]
CATEGORIES = {
    'healthy': (
        'Bounded discovery completed',
        ['No paid repair is indicated by this result.',
         'Do not infer that tools execute successfully: tools/call was not tested.']
    ),
    'timeout': (
        'Request timed out',
        ['Check network reachability, DNS/TLS, and the server request deadline.',
         'Separate initialize, tools/list and a slow tool execution; this probe only tests discovery.']
    ),
    'connection': (
        'Connection failed',
        ['Check your endpoint URL, DNS and TLS from your own environment.',
         'Confirm the service is listening; do not disable TLS verification.']
    ),
    'authentication': (
        'Endpoint rejected authorization',
        ['Check the correct auth scope and endpoint; keep credentials in a local environment variable.',
         'Do not publish tokens, override a 401/403, or automatically retry payment.']
    ),
    'not_found': (
        'HTTP endpoint not found',
        ['Check that the URL points to the MCP Streamable HTTP endpoint, not the homepage.',
         'Verify the route in the server documentation before repeating an authorized check.']
    ),
    'http_server': (
        'Server HTTP error',
        ['Inspect the server logs you control and identify the failed request.',
         'An HTTP status alone does not establish why the MCP handshake failed.']
    ),
    'http_other': (
        'Unexpected HTTP response',
        ['Inspect the response status and your endpoint contract locally.',
         'Do not assume a successful HTTP response means the MCP handshake succeeded.']
    ),
    'rpc_contract': (
        'JSON-RPC contract mismatch',
        ['Verify JSON-RPC response IDs, the result/error envelope, and the protocol revision.',
         'Reproduce with a synthetic server response before changing production code.']
    ),
    'tool_contract': (
        'Tool discovery contract mismatch',
        ['Inspect the advertised tools capability, tools/list shape, and inputSchema objects.',
         'This probe checks descriptors only; it does not execute or certify tools.']
    ),
    'protocol': (
        'MCP protocol negotiation failed',
        ['Compare server and client MCP protocol revisions.',
         'This probe supports only the three revisions stated in its documentation.']
    ),
    'configuration': (
        'Local probe configuration issue',
        ['Check the CLI URL, authorization flag and any token environment variable.',
         'Fix local configuration before considering any hosted repair.']
    ),
    'interrupted': (
        'Diagnostic interrupted',
        ['Retry only after checking that the authorized endpoint is safe to probe.',
         'An interrupted run does not prove the service is unhealthy.']
    ),
    'unknown': (
        'Bounded discovery failed; root cause undetermined',
        DEFAULT_STEPS
    ),
}
TOOL_ISSUES = {
    'tools/list lacks a tools array',
    'invalid tool descriptor',
    'tool inputSchema must describe an object',
    'duplicate tool name across discovery pages',
    'invalid or repeated pagination cursor',
    'tools/list exceeds 10-page bound; discovery incomplete',
    'invalid tools capability',
}
RPC_ISSUES = {
    'mismatched request ID or invalid response shape',
    'invalid JSON-RPC envelope',
    'JSON-RPC result must be an object',
    'response is not valid UTF-8 JSON',
    'unsupported response content type',
    'server-initiated requests are not supported by this probe',
    'SSE stream ended before the matching response',
    'SSE response deadline exceeded',
    'SSE response exceeds size limit',
    'SSE response is not valid UTF-8',
    'response exceeds 1 MiB limit',
}


def classify(report):
    if report['status'] == 'pass':
        return 'healthy'
    error = report.get('error') or {}
    if error.get('code') == 'configuration_error':
        return 'configuration'
    if error.get('code') == 'interrupted':
        return 'interrupted'
    message = error.get('message')
    # Never print the message: even an edited report could contain a token.
    if not isinstance(message, str) or len(message) > 180:
        return 'unknown'
    if message in TOOL_ISSUES:
        return 'tool_contract'
    if message in RPC_ISSUES or re.fullmatch(
            r'JSON-RPC error code -?[0-9]{1,9} \(server message omitted\)', message):
        return 'rpc_contract'
    if message in ('network read/connect timeout',):
        return 'timeout'
    if message in ('connection failed; check DNS, TLS, URL, and reachability',
                   'redirect refused; use the canonical MCP endpoint'):
        return 'connection'
    if message in ('server selected a protocol revision unsupported by this probe',
                   'initialize lacks capabilities or serverInfo', 'invalid serverInfo'):
        return 'protocol'
    m = re.fullmatch(r'HTTP ([1-5][0-9]{2}) \(response body omitted\)', message)
    if m:
        code = int(m.group(1))
        if code in (401, 403):
            return 'authentication'
        if code == 404:
            return 'not_found'
        if 500 <= code <= 599:
            return 'http_server'
        return 'http_other'
    if message in ('request must return HTTP 200', 'notification must return empty HTTP 202',
                   'invalid session header'):
        return 'rpc_contract'
    return 'unknown'


def _revision(report, field):
    value = report.get(field)
    return value if isinstance(value, str) and value in PROTOCOLS else None


def make_passport(report, *, include_optional_service=False, source='offline'):
    # Reuse the project's established validation, discarding its text output.
    # It rejects inconsistent status, malformed requests and tool execution.
    validate_probe_report(report)
    category = classify(report)
    status = report['status']
    method = report['error'].get('method') if status == 'fail' else None
    events = [{'method': item['method'], 'http_status': item['http_status']}
              for item in report['requests']]
    count = report.get('tool_count')
    count = count if type(count) is int and 0 <= count <= 100000 else None
    safe_evidence = {
        'probe_status': status,
        'requested_protocol': _revision(report, 'requested_protocol_version'),
        'negotiated_protocol': _revision(report, 'negotiated_protocol_version'),
        'session_present': report.get('session_present')
            if type(report.get('session_present')) is bool else None,
        'tools_advertised': report.get('tools_advertised')
            if type(report.get('tools_advertised')) is bool else None,
        'tool_count': count,
        'requests': events,
        'failed_at': method,
        'failure_category': category,
        'tools_executed': False,
    }
    # A stable grouping label, not a signed report, user identity or proof.
    canonical = json.dumps(safe_evidence, sort_keys=True,
                           separators=(',', ':'), ensure_ascii=True).encode('ascii')
    fingerprint = hashlib.sha256(canonical).hexdigest()[:20]
    label, free_steps = CATEGORIES[category]
    result = {
        'schema_version': '1.0',
        'product': 'NAIF Error Passport',
        'mode': source,
        'result': 'BOUNDED_DISCOVERY_PASS' if status == 'pass' else 'DIAGNOSIS_ONLY',
        'category': category,
        'finding': label,
        'fingerprint': 'sha256-prefix:' + fingerprint,
        'evidence': safe_evidence,
        'free_next_steps': list(free_steps),
        'free_guide': None if status == 'pass' else DIAGNOSTIC_GUIDE,
        'scope': 'MCP Streamable HTTP initialize and tools/list discovery only',
        'limitations': [
            'Self-reported diagnostic; hash groups identical observations, not verified identities or security proof.',
            'No tools/call, functional repair, signed proof, full MCP conformance or customer data validation.',
            'No remote upload or automatic checkout; use only authorized endpoints with redacted inputs.',
        ],
        'automatic_payment': False,
        'automatic_repair': False,
    }
    if include_optional_service and category in (
            'timeout', 'http_server', 'http_other', 'rpc_contract',
            'tool_contract', 'protocol', 'unknown'):
        result['optional_service'] = {
            'url': OPTIONAL_SERVICE,
            'note': 'Optional scope review only. Check the current quote and eligibility; '
                    'the operator must separately authorize any purchase.',
        }
    return result


def markdown(passport):
    e = passport['evidence']
    lines = [
        '# NAIF Error Passport',
        '',
        '- Result: ' + passport['result'],
        '- Finding: ' + passport['finding'],
        '- Local fingerprint: ' + passport['fingerprint'],
        '- Requested MCP revision: ' + (e['requested_protocol'] or 'unavailable'),
        '- Negotiated MCP revision: ' + (e['negotiated_protocol'] or 'unavailable'),
        '- Advertised tools: ' + (
            'yes' if e['tools_advertised'] is True else
            'no' if e['tools_advertised'] is False else 'unknown'),
        '- Complete tool count: ' + (
            str(e['tool_count']) if e['tool_count'] is not None else 'not available'),
        '- Failed at: ' + (e['failed_at'] or 'not applicable'),
        '- Tools executed: no',
        '',
        '## Bounded HTTP observations',
        '',
        '| Request | HTTP status |',
        '| --- | --- |',
    ]
    lines.extend('| ' + event['method'] + ' | ' + str(event['http_status']) + ' |'
                 for event in e['requests'])
    if not e['requests']:
        lines.append('| No response recorded | — |')
    lines += ['', '## Free next steps', '']
    lines += ['- ' + line for line in passport['free_next_steps']]
    if passport.get('free_guide'):
        lines += ['- Free guide: ' + passport['free_guide']]
    if passport.get('optional_service'):
        lines += ['', '## Optional scoped service', '',
                  passport['optional_service']['url'],
                  '',
                  passport['optional_service']['note']]
    lines += ['', '## Limits', '']
    lines += ['- ' + item for item in passport['limitations']]
    lines += ['', 'Generated locally. No checkout, upload or remote repair was initiated.', '']
    return '\n'.join(lines)


def read_report(location):
    if location == '-':
        data = sys.stdin.buffer.read(MAX_INPUT + 1)
    else:
        with open(location, 'rb') as f:
            data = f.read(MAX_INPUT + 1)
    if len(data) > MAX_INPUT:
        raise ValueError('probe report too large')
    return json.loads(data.decode('utf-8'))


def run_bounded_probe(endpoint, timeout, token_env):
    url = urllib.parse.urlsplit(endpoint)
    # Avoid putting credential-bearing URLs in CI logs or local report metadata.
    if (not url.hostname or url.username or url.password or url.query or url.fragment
            or url.scheme not in ('http', 'https')
            or (url.scheme == 'http' and url.hostname not in (
                'localhost', '127.0.0.1', '::1'))):
        raise ValueError('authorized HTTPS URL or HTTP loopback URL required without secrets')
    cmd = [sys.executable, str(Path(__file__).with_name('mcp_health_check.py')),
           endpoint, '--json', '--timeout', str(timeout)]
    if token_env:
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,70}', token_env):
            raise ValueError('invalid token environment variable name')
        cmd.extend(['--token-env', token_env])
    try:
        completed = subprocess.run(cmd, capture_output=True, timeout=timeout * 14 + 10,
                                   check=False)
    except subprocess.TimeoutExpired:
        raise ValueError('probe exceeded total time budget') from None
    if completed.returncode not in (0, 1) or len(completed.stdout) > MAX_INPUT:
        raise ValueError('probe exited unexpectedly or returned oversized data')
    report = json.loads(completed.stdout.decode('utf-8'))
    if report.get('exit_code') != completed.returncode:
        raise ValueError('inconsistent probe process status')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--report', metavar='FILE', help='existing sanitized JSON report or -')
    group.add_argument('--probe', metavar='URL', help='explicitly authorized MCP endpoint')
    parser.add_argument('--authorized', action='store_true',
                        help='required to start any network probe')
    parser.add_argument('--timeout', type=int, choices=range(1, 21),
                        metavar='1-20', default=10)
    parser.add_argument('--token-env', metavar='ENV_NAME')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--show-optional-service', action='store_true',
                        help='show an optional scoped service only on relevant failure')
    args = parser.parse_args(argv)
    if args.probe and not args.authorized:
        parser.error('--probe requires --authorized (explicit endpoint permission)')
    if args.report and (args.authorized or args.token_env):
        parser.error('--authorized/--token-env apply to --probe only')
    try:
        report = (run_bounded_probe(args.probe, args.timeout, args.token_env)
                  if args.probe else read_report(args.report))
        passport = make_passport(report, include_optional_service=args.show_optional_service,
                                 source='authorized-local-probe' if args.probe else 'offline')
        print(json.dumps(passport, sort_keys=True, indent=2) if args.format == 'json'
              else markdown(passport), end='\n' if args.format == 'json' else '')
        return 0 if passport['result'] == 'BOUNDED_DISCOVERY_PASS' else 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError,
            UnicodeError, subprocess.SubprocessError):
        # Never emit user report bodies, server messages, paths or credential details.
        print('Invalid or unavailable sanitized MCP discovery report; no passport created.',
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
