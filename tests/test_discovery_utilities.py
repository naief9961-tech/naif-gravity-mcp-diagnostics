import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
lab = load('lab', 'examples/fault_lab.py')
drafts = load('drafts', 'tools/issue_report.py')
class DiscoveryUtilitiesTests(unittest.TestCase):
    def test_all_faults_are_detected_without_tool_execution(self):
        for name in lab.CASES:
            with self.subTest(case=name):
                result = lab.run_case(name)
                self.assertTrue(result['verified'])
                self.assertFalse(result['report']['tools_executed'])
                self.assertEqual(result['report']['exit_code'], result['expected_exit_code'])
                draft = drafts.render(result['report'])
                self.assertIn('Result: ' + result['report']['status'], draft)
                for private in ('fixture-secret', 'fixture-session', '127.0.0.1'):
                    self.assertNotIn(private, draft)
    def test_draft_excludes_injected_messages_and_metadata(self):
        report = lab.run_case('wrong-id')['report']
        secret = 'PRIVATE-TOKEN-https://internal.example/private'
        report['error']['message'] = secret
        report['private_url'] = secret
        report['requested_protocol_version'] = secret
        report['negotiated_protocol_version'] = secret
        report['requests'][0]['body'] = secret
        self.assertNotIn(secret, drafts.render(report))
        report['requests'][0]['method'] = secret
        with self.assertRaises(ValueError):
            drafts.render(report)
    def test_rejects_inconsistent_or_non_probe_reports(self):
        base = lab.run_case('healthy')['report']
        for changes in ({'schema_version': '2'}, {'exit_code': 1}, {'tools_executed': True},
                        {'requests': [{'method': 'tools/call', 'http_status': 200}]},
                        {'requests': [{'method': 'initialize', 'http_status': True}]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                drafts.render(dict(base, **changes))
        with self.assertRaises(ValueError):
            drafts.render({'lab_schema_version': '1.0'})
    def test_cli_stdin_failure_is_sanitized_and_bounded(self):
        for data in (b'private-token-not-json', b'x' * (drafts.MAX_INPUT + 1)):
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/issue_report.py')], input=data, capture_output=True, timeout=5)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(proc.stdout, b'')
            self.assertNotIn(b'private-token', proc.stderr)
    def test_single_fault_report_exit_and_pipe_to_draft(self):
        probe = subprocess.run([sys.executable, str(ROOT / 'examples/fault_lab.py'), '--case', 'wrong-id', '--report'], capture_output=True, timeout=10)
        self.assertEqual(probe.returncode, 1)
        self.assertEqual(json.loads(probe.stdout)['status'], 'fail')
        result = subprocess.run([sys.executable, str(ROOT / 'tools/issue_report.py')], input=probe.stdout, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'discovery_failed at initialize', result.stdout)
    def test_lab_json_and_expected_failure_exit_semantics(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(lab.main(['--case', 'wrong-id', '--json']), 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result['verified'])
        self.assertEqual(result['cases'][0]['report']['exit_code'], 1)
if __name__ == '__main__':
    unittest.main()
