#!/usr/bin/env python3
"""Compare two bounded MCP probe reports offline. No network or deployment actions."""
import argparse
import json
import sys
from pathlib import Path

MAX_BYTES = 1024 * 1024
VERSIONS = {'2025-03-26', '2025-06-18', '2025-11-25'}
METHODS = {'initialize', 'notifications/initialized', 'tools/list'}
CODES = {'configuration_error', 'discovery_failed', 'interrupted'}


def validate(report):
    if not isinstance(report, dict) or report.get('schema_version') != '1.0':
        raise ValueError('invalid schema')
    status = report.get('status')
    if (status not in ('pass', 'fail') or type(report.get('exit_code')) is not int
            or report['exit_code'] != (0 if status == 'pass' else 1)
            or report.get('tools_executed') is not False):
        raise ValueError('invalid status')
    requested = report.get('requested_protocol_version')
    if not isinstance(requested, str) or requested not in VERSIONS:
        raise ValueError('invalid requested revision')
    negotiated = report.get('negotiated_protocol_version')
    if negotiated is not None and (not isinstance(negotiated, str) or len(negotiated) > 64):
        raise ValueError('invalid negotiated revision')
    for key in ('session_present', 'tools_advertised'):
        if report.get(key) is not None and type(report[key]) is not bool:
            raise ValueError('invalid boolean')
    count = report.get('tool_count')
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError('invalid count')
    events = report.get('requests')
    if not isinstance(events, list) or len(events) > 12:
        raise ValueError('invalid observations')
    trace = []
    for event in events:
        if (not isinstance(event, dict) or not isinstance(event.get('method'), str)
                or event['method'] not in METHODS or type(event.get('http_status')) is not int
                or not 100 <= event['http_status'] <= 599):
            raise ValueError('invalid observation')
        trace.append((event['method'], event['http_status']))
    error = report.get('error')
    if status == 'pass':
        if (error is not None or negotiated not in VERSIONS
                or type(report.get('session_present')) is not bool
                or type(report.get('tools_advertised')) is not bool
                or (report['tools_advertised'] and count is None)
                or (not report['tools_advertised'] and count is not None)):
            raise ValueError('inconsistent successful report')
        expected = ['initialize', 'notifications/initialized']
        if report['tools_advertised']:
            if len(trace) < 3 or any(method != 'tools/list' for method, _ in trace[2:]):
                raise ValueError('missing discovery observations')
            expected += ['tools/list'] * (len(trace) - 2)
        if [method for method, _ in trace] != expected or any(not 200 <= code < 300 for _, code in trace):
            raise ValueError('inconsistent successful observations')
    else:
        if (not isinstance(error, dict) or not isinstance(error.get('code'), str)
                or error['code'] not in CODES
                or (error.get('method') is not None and
                    (not isinstance(error['method'], str) or error['method'] not in METHODS))):
            raise ValueError('invalid failure category')
    # Return only allowlisted fields; never echo input messages or arbitrary metadata.
    return {'status': status, 'requested': requested,
            'negotiated': negotiated if negotiated in VERSIONS else None,
            'session': report.get('session_present'), 'advertised': report.get('tools_advertised'),
            'count': count, 'trace': trace}


def compare(before, after, strict_changes=False):
    before, after = validate(before), validate(after)
    if before['status'] != 'pass':
        raise ValueError('baseline must be healthy')
    if before['requested'] != after['requested']:
        raise ValueError('requested revisions differ')
    regressions, changes = [], []
    if after['status'] == 'fail':
        regressions.append('discovery_failed_after_healthy_baseline')
    else:
        if before['advertised'] and not after['advertised']:
            regressions.append('tools_capability_lost')
        elif before['advertised'] and after['advertised'] and after['count'] < before['count']:
            regressions.append('tool_count_decreased')
        if before['advertised'] != after['advertised']:
            changes.append('tools_capability_changed')
        if before['count'] != after['count']:
            changes.append('tool_count_changed')
        if before['negotiated'] != after['negotiated']:
            changes.append('negotiated_revision_changed')
        if before['session'] != after['session']:
            changes.append('session_presence_changed')
        if before['trace'] != after['trace']:
            changes.append('http_discovery_observations_changed')
    status = 'regression' if regressions else 'changed' if changes else 'unchanged'
    code = 1 if regressions or (strict_changes and changes) else 0
    return {'guard_schema_version': '1.0', 'status': status, 'exit_code': code,
            'regressions': regressions, 'changes': changes, 'strict_changes': strict_changes,
            'network_requests': False, 'tools_executed': False}


def read_report(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('oversized input')
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='healthy baseline probe JSON file')
    parser.add_argument('after', help='current probe JSON file for the same endpoint/configuration')
    parser.add_argument('--json', action='store_true', help='emit one bounded JSON comparison')
    parser.add_argument('--strict-changes', action='store_true', help='exit 1 for any observed change, including healthy changes')
    args = parser.parse_args(argv)
    try:
        result = compare(read_report(args.before), read_report(args.after), args.strict_changes)
    except (OSError, ValueError, TypeError, RecursionError):
        result = {'guard_schema_version': '1.0', 'status': 'inconclusive', 'exit_code': 2,
                  'reason': 'invalid_reports_or_unhealthy_baseline_or_different_requested_revisions',
                  'network_requests': False, 'tools_executed': False}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print('Guard: ' + result['status'] + ' (exit ' + str(result['exit_code']) + ')')
        for key in ('regressions', 'changes'):
            for item in result.get(key, []):
                print(key + ': ' + item)
        if result['exit_code'] == 2:
            print('Use valid probe schema 1.0 reports, a healthy baseline and the same requested revision.')
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
