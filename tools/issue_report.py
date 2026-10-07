#!/usr/bin/env python3
"""Convert probe JSON into a small Markdown draft; never submits an issue."""
import argparse
import json
import sys
from pathlib import Path

MAX_INPUT = 1024 * 1024
METHODS = {'initialize', 'notifications/initialized', 'tools/list'}
VERSIONS = {'2025-03-26', '2025-06-18', '2025-11-25'}
CODES = {'configuration_error', 'discovery_failed', 'interrupted'}


def render(report):
    if not isinstance(report, dict) or report.get('schema_version') != '1.0':
        raise ValueError('expected probe schema_version 1.0')
    status, exit_code = report.get('status'), report.get('exit_code')
    if status not in ('pass', 'fail') or type(exit_code) is not int or exit_code != (0 if status == 'pass' else 1):
        raise ValueError('inconsistent probe status and exit code')
    if report.get('tools_executed') is not False:
        raise ValueError('expected discovery-only report')
    requests = report.get('requests')
    if not isinstance(requests, list) or len(requests) > 12:
        raise ValueError('invalid or oversized request observations')
    rows = []
    for event in requests:
        if (not isinstance(event, dict) or event.get('method') not in METHODS
                or type(event.get('http_status')) is not int or not 100 <= event['http_status'] <= 599):
            raise ValueError('invalid request observation')
        rows.append('| ' + event['method'] + ' | ' + str(event['http_status']) + ' |')
    def revision(key):
        value = report.get(key)
        return value if isinstance(value, str) and value in VERSIONS else 'unknown / unsupported / not negotiated'
    count = report.get('tool_count')
    count = str(count) if type(count) is int and 0 <= count <= 100000 else 'not available'
    error = report.get('error')
    if status == 'fail':
        if not isinstance(error, dict) or error.get('code') not in CODES:
            raise ValueError('invalid failure code')
        method = error.get('method')
        if method is not None and method not in METHODS:
            raise ValueError('invalid failure method')
        failure = error['code'] + ' at ' + (method or 'configuration / before request')
    else:
        if error is not None:
            raise ValueError('unexpected error on successful report')
        failure = 'none'
    # Deliberately ignore error.message and all arbitrary metadata, even in edited input.
    return '\n'.join([
        '# MCP discovery diagnostic draft', '',
        '## Expected behavior', '',
        'Complete initialize, initialized notification and tools/list when advertised, without executing tools.', '',
        '## Observed behavior', '',
        '- Result: ' + status + ' (exit ' + str(exit_code) + ')',
        '- Requested revision: ' + revision('requested_protocol_version'),
        '- Negotiated revision: ' + revision('negotiated_protocol_version'),
        '- Complete tool count: ' + count,
        '- Failure category: ' + failure,
        '- Tools executed: no', '',
        '| Method | HTTP status |', '| --- | --- |',
        *(rows or ['| No HTTP response recorded | — |']), '',
        '## Reproduction to complete before sharing', '',
        '- Add a minimal synthetic reproduction and the exact probe commit you used.',
        '- Add Python and operating-system versions, and the server implementation/version.',
        '- Run: `python3 tools/mcp_health_check.py <authorized-endpoint> --json`',
        '- For auth, add `--token-env MCP_TEST_TOKEN`; never paste its value.', '',
        'This is a bounded discovery observation, not a full conformance verdict. '
        'Review the draft and replace private endpoints with placeholders before sharing.', '',
        'Generated locally by NAIF Gravity MCP Diagnostics. No issue was submitted.', ''])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', default='-', help='probe JSON file, or - for stdin')
    args = parser.parse_args(argv)
    try:
        if args.input == '-':
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        else:
            with Path(args.input).open('rb') as stream:
                raw = stream.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError('input exceeds 1 MiB')
        draft = render(json.loads(raw))
    except (OSError, ValueError, TypeError, RecursionError):
        print('Cannot generate draft: expected a valid bounded probe JSON report (schema 1.0).', file=sys.stderr)
        return 2
    print(draft, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
