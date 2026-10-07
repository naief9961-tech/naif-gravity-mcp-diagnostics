#!/usr/bin/env python3
"""Run the probe against synthetic loopback fixtures; no external services.

Reuse the integration-test fixtures so examples and verified behavior agree.
Run from a complete checkout: python3 examples/mcp_discovery_demo.py
"""
import importlib.util
from pathlib import Path


def main():
    path = Path(__file__).resolve().parents[1] / 'tests/test_mcp_health_check.py'
    spec = importlib.util.spec_from_file_location('demo_fixtures', path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    for mode, expected in (('json', 0), ('wrong-id', 1)):
        print('\nScenario: ' + mode)
        with fixtures.fixture(mode) as (url, requests):
            status = fixtures.health.main([url, '--timeout', '3'])
        print('probe exit: ' + str(status))
        print('requests: ' + ' -> '.join(msg['method'] for msg, _ in requests))
        if status != expected or any(msg['method'] == 'tools/call' for msg, _ in requests):
            raise RuntimeError('demo did not match its expected bounded behavior')
    print('\nDemo verified: healthy discovery passes; HTTP 200 with a wrong ID fails.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
