"""Offline guard policy, input validation and non-disclosure tests."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('guard', ROOT / 'tools/integration_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

def report():
    return {'schema_version':'1.0','status':'pass','exit_code':0,
            'requested_protocol_version':'2025-06-18','negotiated_protocol_version':'2025-11-25',
            'session_present':True,'tools_advertised':True,'tool_count':2,'tools_executed':False,
            'requests':[{'method':'initialize','http_status':200},
                        {'method':'notifications/initialized','http_status':202},
                        {'method':'tools/list','http_status':200}], 'error':None}

class GuardTests(unittest.TestCase):
    def test_unchanged(self):
        self.assertEqual(guard.compare(report(), report())['status'], 'unchanged')
    def test_failed_discovery_is_regression(self):
        current = report()
        current.update(status='fail',exit_code=1,tool_count=None,
                       error={'code':'discovery_failed','method':'initialize','message':'PRIVATE'})
        result=guard.compare(report(),current)
        self.assertEqual(result['exit_code'],1)
        self.assertIn('discovery_failed_after_healthy_baseline',result['regressions'])
        self.assertNotIn('PRIVATE',json.dumps(result))
    def test_tool_count_decrease_and_capability_loss(self):
        current=report(); current['tool_count']=1
        self.assertIn('tool_count_decreased',guard.compare(report(),current)['regressions'])
        current.update(tools_advertised=False,tool_count=None,requests=current['requests'][:2])
        self.assertIn('tools_capability_lost',guard.compare(report(),current)['regressions'])
    def test_healthy_changes_warn_and_strict_blocks(self):
        for change in ({'tool_count':3},{'session_present':False},{'negotiated_protocol_version':'2025-06-18'}):
            current=dict(report(),**change)
            self.assertEqual(guard.compare(report(),current)['exit_code'],0)
            self.assertEqual(guard.compare(report(),current)['status'],'changed')
            self.assertEqual(guard.compare(report(),current,True)['exit_code'],1)
        current=report(); current['requests'][1]['http_status']=204
        self.assertIn('http_discovery_observations_changed',guard.compare(report(),current)['changes'])
    def test_invalid_and_incomparable_inputs(self):
        for change in ({'tools_executed':True},{'exit_code':1},{'tool_count':True},
                       {'session_present':'PRIVATE'},{'negotiated_protocol_version':[]},
                       {'requests':[]},{'error':{'message':'PRIVATE'}},{'schema_version':'2'},
                       {'requested_protocol_version':'2025-11-25'}):
            with self.subTest(change=change),self.assertRaises((ValueError,TypeError)):
                guard.compare(report(),dict(report(),**change))
        unhealthy=report(); unhealthy.update(status='fail',exit_code=1,error={'code':'interrupted','method':None})
        with self.assertRaises(ValueError):
            guard.compare(unhealthy,report())
    def test_free_text_metadata_is_ignored(self):
        before=report(); after=copy.deepcopy(before)
        after['private_url']='PRIVATE'; after['requests'][0]['body']='PRIVATE'
        result=guard.compare(before,after)
        self.assertEqual(result['status'],'unchanged')
        self.assertNotIn('PRIVATE',json.dumps(result))
    def test_cli_codes_json_and_size_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            before=Path(temp)/'before.json'; after=Path(temp)/'after.json'
            before.write_text(json.dumps(report()))
            for content,expected in ((json.dumps(report()),0),
                                     (json.dumps(dict(report(),tool_count=1)),1),
                                     ('PRIVATE invalid',2),('x'*(guard.MAX_BYTES+1),2)):
                after.write_text(content)
                result=subprocess.run([sys.executable,str(ROOT/'tools/integration_guard.py'),str(before),str(after),'--json'],capture_output=True,timeout=5)
                self.assertEqual(result.returncode,expected)
                self.assertEqual(json.loads(result.stdout)['exit_code'],expected)
                self.assertNotIn(b'PRIVATE',result.stdout+result.stderr)

if __name__=='__main__':
    unittest.main()
