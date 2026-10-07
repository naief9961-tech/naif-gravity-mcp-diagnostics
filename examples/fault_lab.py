#!/usr/bin/env python3
"""Reproduce seven MCP discovery cases on temporary loopback servers."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path

CASES = {
    'healthy': ('json', 0, 'A valid discovery sequence completes.', 'Keep this as a control when comparing a failing implementation.'),
    'missing-token': ('auth', 1, 'The server rejects an unauthenticated initialize request with HTTP 401.', 'Provision a scoped test token via --token-env; never paste tokens into an issue.'),
    'wrong-id': ('wrong-id', 1, 'HTTP 200 carries a response ID that does not match the request.', 'Echo the request ID in its response; do not treat HTTP success as RPC success.'),
    'invalid-json': ('malformed-json', 1, 'HTTP 200 carries a body that is not valid JSON.', 'Check gateway routing and response serialization; inspect bodies privately.'),
    'unsupported-version': ('unsupported-version', 1, 'The server selects a revision this probe does not support.', 'Check both supported revision sets; this can be a probe limitation, not a server defect.'),
    'cursor-loop': ('cursor-loop', 1, 'tools/list keeps returning the same pagination cursor.', 'Return a progressing cursor and omit nextCursor on the final page.'),
    'invalid-tool-schema': ('bad-schema', 1, 'A tool inputSchema declares a string instead of an object.', 'Declare an object input schema and validate descriptors before publishing them.'),
}


def run_case(name):
    path = Path(__file__).resolve().parents[1] / 'tests/test_mcp_health_check.py'
    spec = importlib.util.spec_from_file_location('fault_lab_fixtures', path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    mode, expected, explanation, repair = CASES[name]
    with fixtures.fixture(mode) as (url, requests), contextlib.redirect_stdout(io.StringIO()) as out:
        status = fixtures.health.main([url, '--timeout', '3', '--json'])
    report = json.loads(out.getvalue())
    allowed = {'initialize', 'notifications/initialized', 'tools/list'}
    verified = status == expected and all(req[0]['method'] in allowed for req in requests)
    return {'case': name, 'expected_exit_code': expected, 'verified': verified,
            'explanation': explanation, 'next_check': repair, 'report': report}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, help='run one case; default runs all')
    parser.add_argument('--json', action='store_true', help='emit the full lab result as one JSON document')
    parser.add_argument('--report', action='store_true', help='with --case: emit only probe JSON and return its exit code')
    args = parser.parse_args(argv)
    if args.report and (not args.case or args.json):
        parser.error('--report requires --case and cannot be combined with --json')
    results = [run_case(name) for name in ([args.case] if args.case else CASES)]
    if args.report:
        print(json.dumps(results[0]['report'], sort_keys=True))
        return results[0]['report']['exit_code']
    verified = all(result['verified'] for result in results)
    if args.json:
        print(json.dumps({'lab_schema_version': '1.0', 'verified': verified, 'cases': results}, sort_keys=True))
    else:
        for result in results:
            print(('VERIFIED' if result['verified'] else 'UNEXPECTED') + ': ' + result['case'])
            print('  ' + result['explanation'])
            print('  Next check: ' + result['next_check'])
        print('Lab exit 0 means expected outcomes were reproduced, including intentional failures.')
    return 0 if verified else 1


if __name__ == '__main__':
    raise SystemExit(main())
