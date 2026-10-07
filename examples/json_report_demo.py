#!/usr/bin/env python3
"""Emit one JSON report from a synthetic loopback MCP server."""
import argparse
import importlib.util
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--failure', action='store_true', help='simulate HTTP 200 with a wrong response ID (exit 1)')
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / 'tests/test_mcp_health_check.py'
    spec = importlib.util.spec_from_file_location('json_demo_fixtures', path)
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    with fixtures.fixture('wrong-id' if args.failure else 'json') as (url, _):
        return fixtures.health.main([url, '--timeout', '3', '--json'])


if __name__ == '__main__':
    raise SystemExit(main())
