"""Integration tests against loopback fixtures only; no production traffic."""
import contextlib
import importlib.util
import io
import json
import os
import socket
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('health', Path(__file__).parents[1] / 'tools/mcp_health_check.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)
SECRET = 'fixture-secret-never-print'


@contextlib.contextmanager
def fixture(mode='json'):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *_):
            pass

        def reply(self, status, body=b'', kind='application/json', extra=None):
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()

        def do_POST(self):
            msg = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append((msg, dict(self.headers)))
            method = msg['method']
            if mode == 'auth' and self.headers.get('Authorization') != 'Bearer ' + SECRET:
                return self.reply(401, SECRET.encode())
            if mode == 'redirect':
                return self.reply(307, extra={'Location': '/other'})
            if mode == 'http-error':
                return self.reply(403, SECRET.encode())
            if method != 'initialize' and (self.headers.get('Mcp-Session-Id') != 'fixture-session' or self.headers.get('MCP-Protocol-Version') != '2025-11-25'):
                return self.reply(400)
            if method == 'notifications/initialized':
                if mode == 'bad-notification':
                    return self.reply(200)
                return self.reply(202)
            if method == 'tools/list' and not any(x[0]['method'] == 'notifications/initialized' for x in requests):
                return self.reply(400)
            obj = {'jsonrpc': '2.0', 'id': msg['id']}
            if method == 'initialize':
                obj['result'] = {'protocolVersion': '2025-11-25', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'fixture', 'version': '1'}}
                if mode == 'no-tools':
                    obj['result']['capabilities'] = {}
                if mode == 'unsupported-version':
                    obj['result']['protocolVersion'] = '2099-01-01'
                if mode == 'invalid-init':
                    del obj['result']['serverInfo']
            else:
                obj['result'] = {'tools': [{'name': 'fixture_tool', 'inputSchema': {'type': 'object'}}]}
                if mode == 'pagination':
                    if not msg['params'].get('cursor'):
                        obj['result']['nextCursor'] = 'page-2'
                    else:
                        obj['result']['tools'][0]['name'] = 'fixture_tool_2'
                if mode == 'cursor-loop':
                    obj['result']['tools'] = []
                    obj['result']['nextCursor'] = 'same'
                if mode == 'malformed-tools':
                    obj['result']['tools'] = 'not-array'
                if mode == 'bad-schema':
                    obj['result']['tools'][0]['inputSchema'] = {'type': 'string'}
                if mode == 'rpc-error':
                    obj.pop('result')
                    obj['error'] = {'code': -32601, 'message': SECRET}
            if mode == 'wrong-id':
                obj['id'] = 'wrong'
            if mode == 'malformed-json':
                return self.reply(200, b'<html>' + SECRET.encode())
            if mode == 'oversized':
                return self.reply(200, b'x' * (health.MAX_BYTES + 1))
            extra = {'Mcp-Session-Id': 'fixture-session'} if method == 'initialize' else {}
            if mode.startswith('sse'):
                payload = json.dumps(obj, indent=2)
                body = ': heartbeat\r\n\r\ndata: {"jsonrpc":"2.0","method":"notifications/message"}\r\n\r\n'
                body += '\r\n'.join('data: ' + x for x in payload.splitlines()) + '\r\n\r\n'
                if mode == 'sse-missing':
                    body = ': heartbeat\n\n'
                if mode == 'sse-rpc-error':
                    body = 'data: ' + json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'error': {'code': -32600, 'message': SECRET}}) + '\n\n'
                return self.reply(200, body.encode(), 'text/event-stream', extra)
            return self.reply(200, json.dumps(obj).encode(), extra=extra)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port) + '/mcp', requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


class ProbeTests(unittest.TestCase):
    def run_fixture(self, mode, extra=None):
        with fixture(mode) as (url, requests), contextlib.redirect_stdout(io.StringIO()) as out:
            status = health.main([url] + (extra or []))
        text = out.getvalue()
        self.assertNotIn(SECRET, text)
        self.assertTrue(all(x[0]['method'] in ('initialize', 'notifications/initialized', 'tools/list') for x in requests))
        return status, text, requests

    def test_session_lifecycle_and_negotiated_header(self):
        status, output, requests = self.run_fixture('json')
        self.assertEqual(status, 0)
        self.assertIn('tools: 1', output)
        self.assertEqual([x[0]['method'] for x in requests], ['initialize', 'notifications/initialized', 'tools/list'])
        self.assertNotIn('id', requests[1][0])
        self.assertEqual(requests[2][1]['Mcp-Session-Id'], 'fixture-session')
        self.assertEqual(requests[2][1]['Mcp-Protocol-Version'], '2025-11-25')

    def test_sse_comments_multiline_and_notifications(self):
        status, output, _ = self.run_fixture('sse')
        self.assertEqual(status, 0)
        self.assertIn('tools: 1', output)

    def test_authentication_without_token_disclosure(self):
        with patch.dict(os.environ, {'NAIF_TEST_TOKEN': SECRET}):
            self.assertEqual(self.run_fixture('auth', ['--token-env', 'NAIF_TEST_TOKEN'])[0], 0)
        self.assertEqual(self.run_fixture('auth')[0], 1)

    def test_pagination(self):
        status, output, requests = self.run_fixture('pagination')
        self.assertEqual(status, 0)
        self.assertIn('tools: 2', output)
        self.assertEqual(requests[-1][0]['params'], {'cursor': 'page-2'})

    def test_no_tools_capability_is_valid(self):
        status, output, requests = self.run_fixture('no-tools')
        self.assertEqual(status, 0)
        self.assertIn('not advertised', output)
        self.assertEqual(len(requests), 2)

    def test_failures_are_nonzero_and_do_not_leak_bodies(self):
        for mode in ('http-error', 'rpc-error', 'wrong-id', 'malformed-json', 'oversized',
                     'malformed-tools', 'bad-schema', 'unsupported-version', 'invalid-init',
                     'bad-notification', 'cursor-loop', 'sse-missing', 'sse-rpc-error'):
            with self.subTest(mode=mode):
                status, output, _ = self.run_fixture(mode)
                self.assertEqual(status, 1)
                self.assertNotIn('PASS:', output)

    def test_redirect_is_not_followed(self):
        status, output, requests = self.run_fixture('redirect')
        self.assertEqual(status, 1)
        self.assertIn('redirect refused', output)
        self.assertEqual(len(requests), 1)

    def test_configuration_errors_make_no_request(self):
        with patch.object(health.Probe, 'run') as run, contextlib.redirect_stdout(io.StringIO()) as out:
            with patch.dict(os.environ, {'NAIF_TEST_TOKEN': SECRET}):
                self.assertEqual(health.main(['http://example.com/mcp', '--token-env', 'NAIF_TEST_TOKEN']), 1)
                self.assertEqual(health.main(['https://user:password@example.com/mcp']), 1)
                self.assertEqual(health.main(['https://example.com/mcp', '--token-env', 'NAIF_UNSET_TOKEN']), 1)
            run.assert_not_called()
            self.assertNotIn(SECRET, out.getvalue())

    def test_timeout_reports_failure_without_exception_details(self):
        probe = health.Probe('https://fixture.example/mcp')
        with patch.object(probe.opener, 'open', side_effect=socket.timeout(SECRET)):
            with self.assertRaisesRegex(health.ProbeError, 'timeout') as error:
                probe.post('initialize', {})
            self.assertNotIn(SECRET, str(error.exception))

    def test_discovery_page_bound(self):
        probe = health.Probe('https://fixture.example/mcp')
        pages = iter(range(100))
        def post(method, params=None, notification=False):
            if method == 'initialize':
                return {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}},
                        'serverInfo': {'name': 'fixture', 'version': '1'}}
            if notification:
                return None
            page = next(pages)
            return {'tools': [], 'nextCursor': str(page)}
        with patch.object(probe, 'post', side_effect=post), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(health.ProbeError, '10-page'):
                probe.run('2025-06-18')
        self.assertEqual(next(pages), 10)

    def test_sse_matching_response_does_not_require_eof(self):
        class Stream:
            headers = type('Headers', (), {'get_content_type': lambda self: 'text/event-stream'})()
            lines = iter([b'data: {"jsonrpc":"2.0","id":"123","result":{}}\n', b'\n'])
            def readline(self, limit):
                return next(self.lines)  # Additional reads would fail.
        self.assertEqual(health.read_response(Stream(), '123', float('inf')), {})


if __name__ == '__main__':
    unittest.main()
