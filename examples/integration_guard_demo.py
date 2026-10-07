#!/usr/bin/env python3
"""Demonstrate unchanged discovery, a regression and a healthy tool-count change."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    lab = load('guard_demo_lab', 'examples/fault_lab.py')
    guard = load('guard_demo', 'tools/integration_guard.py')
    baseline = lab.run_case('healthy')['report']
    broken = lab.run_case('wrong-id')['report']
    added = dict(baseline, tool_count=2)
    cases = [('unchanged', baseline, False, 0), ('regression', broken, False, 1),
             ('changed', added, False, 0), ('changed', added, True, 1)]
    for expected, current, strict, code in cases:
        result = guard.compare(baseline, current, strict)
        print(result['status'] + ': exit ' + str(result['exit_code']) + ', strict=' + str(strict))
        if result['status'] != expected or result['exit_code'] != code:
            return 1
    print('Expected guard outcomes verified. Tool-count increase was a synthetic report edit.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
