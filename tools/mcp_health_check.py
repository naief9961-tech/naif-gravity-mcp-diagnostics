#!/usr/bin/env python3
"""Bounded discovery-only probe for handshake-era MCP Streamable HTTP.

Python standard library only. No tools/call, repair, or payment requests.
"""
import argparse
import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

VERSIONS = ('2025-03-26', '2025-06-18', '2025-11-25')
MAX_BYTES = 1024 * 1024
MAX_PAGES = 10


class ProbeError(Exception):
    """Safe diagnostic text; never include server bodies or credentials."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProbeError('redirect refused; use the canonical MCP endpoint')


def decode_message(raw):
    try:
        obj = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    except (ValueError, UnicodeError, RecursionError):
        raise ProbeError('response is not valid UTF-8 JSON') from None
    if not isinstance(obj, dict) or obj.get('jsonrpc') != '2.0':
        raise ProbeError('invalid JSON-RPC envelope')
    return obj


def response_result(obj, request_id):
    if obj.get('id') != request_id or ('result' in obj) == ('error' in obj):
        raise ProbeError('mismatched request ID or invalid response shape')
    if 'error' in obj:
        err = obj['error']
        code = err.get('code') if isinstance(err, dict) else None
        label = str(code) if type(code) is int else 'unknown'
        raise ProbeError('JSON-RPC error code ' + label + ' (server message omitted)')
    if not isinstance(obj['result'], dict):
        raise ProbeError('JSON-RPC result must be an object')
    return obj['result']


def read_response(res, request_id, deadline):
    content_type = res.headers.get_content_type()
    if content_type == 'application/json':
        raw = res.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ProbeError('response exceeds 1 MiB limit')
        return response_result(decode_message(raw), request_id)
    if content_type != 'text/event-stream':
        raise ProbeError('unsupported response content type')
    # Stop on the matching response, even if the stream remains open.
    data, consumed = [], 0
    while True:
        if time.monotonic() > deadline:
            raise ProbeError('SSE response deadline exceeded')
        line = res.readline(min(MAX_BYTES - consumed + 1, 65537))
        consumed += len(line)
        if consumed > MAX_BYTES or len(line) > 65536:
            raise ProbeError('SSE response exceeds size limit')
        if not line:
            raise ProbeError('SSE stream ended before the matching response')
        try:
            line = line.decode('utf-8-sig' if consumed == len(line) else 'utf-8').rstrip('\r\n')
        except UnicodeError:
            raise ProbeError('SSE response is not valid UTF-8') from None
        if line == '':
            if data:
                obj = decode_message('\n'.join(data))
                data = []
                if obj.get('id') == request_id and ('result' in obj or 'error' in obj):
                    return response_result(obj, request_id)
                if 'method' in obj and 'id' in obj:
                    raise ProbeError('server-initiated requests are not supported by this probe')
            continue
        if line.startswith(':'):
            continue
        field, _, value = line.partition(':')
        if field == 'data':
            data.append(value[1:] if value.startswith(' ') else value)


class Probe:
    def __init__(self, url, timeout=10, token=None, json_output=False):
        self.url, self.timeout, self.token = url, timeout, token
        self.version = self.session = None
        self.opener = urllib.request.build_opener(NoRedirect())
        self.json_output = json_output
        self.events = []
        self.active_method = None
        self.tools_advertised = self.tool_count = None

    def log(self, text):
        if not self.json_output:
            print(text)

    def post(self, method, params=None, notification=False):
        self.active_method = method
        request_id = str(uuid.uuid4())
        message = {'jsonrpc': '2.0', 'method': method}
        if not notification:
            message['id'] = request_id
        if params is not None:
            message['params'] = params
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream',
                   'User-Agent': 'naif-gravity-mcp-health-check/2.0'}
        if self.version:
            headers['MCP-Protocol-Version'] = self.version
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        req = urllib.request.Request(self.url, json.dumps(message).encode(), headers, method='POST')
        deadline = time.monotonic() + self.timeout
        try:
            with self.opener.open(req, timeout=self.timeout) as res:
                self.events.append({'method': method, 'http_status': res.status})
                self.log('[' + method + '] HTTP ' + str(res.status))
                if notification:
                    if res.status != 202 or res.read(1):
                        raise ProbeError('notification must return empty HTTP 202')
                    return None
                if res.status != 200:
                    raise ProbeError('request must return HTTP 200')
                result = read_response(res, request_id, deadline)
                if method == 'initialize':
                    session = res.headers.get('Mcp-Session-Id')
                    if session and not all(0x21 <= ord(c) <= 0x7e for c in session):
                        raise ProbeError('invalid session header')
                    self.session = session
                return result
        except urllib.error.HTTPError as e:
            code = e.code
            self.events.append({'method': method, 'http_status': code})
            e.close()
            raise ProbeError('HTTP ' + str(code) + ' (response body omitted)') from None
        except (socket.timeout, TimeoutError):
            raise ProbeError('network read/connect timeout') from None
        except (urllib.error.URLError, OSError, http.client.HTTPException):
            raise ProbeError('connection failed; check DNS, TLS, URL, and reachability') from None

    def run(self, requested_version):
        init = self.post('initialize', {'protocolVersion': requested_version, 'capabilities': {},
                        'clientInfo': {'name': 'naif-gravity-health-check', 'version': '2.0'}})
        version = init.get('protocolVersion')
        if version not in VERSIONS:
            raise ProbeError('server selected a protocol revision unsupported by this probe')
        capabilities = init.get('capabilities')
        info = init.get('serverInfo')
        if not isinstance(capabilities, dict) or not isinstance(info, dict):
            raise ProbeError('initialize lacks capabilities or serverInfo')
        if not all(isinstance(info.get(k), str) and info[k] for k in ('name', 'version')):
            raise ProbeError('invalid serverInfo')
        self.version = version
        self.log('protocol: ' + version)
        self.log('session: ' + ('present' if self.session else 'not assigned'))
        self.tools_advertised = 'tools' in capabilities
        self.post('notifications/initialized', notification=True)
        if 'tools' not in capabilities:
            self.log('tools: not advertised; discovery complete')
            return
        if not isinstance(capabilities['tools'], dict):
            raise ProbeError('invalid tools capability')
        cursor, seen, names, count = None, set(), set(), 0
        for _ in range(MAX_PAGES):
            result = self.post('tools/list', {'cursor': cursor} if cursor else {})
            tools = result.get('tools')
            if not isinstance(tools, list):
                raise ProbeError('tools/list lacks a tools array')
            for tool in tools:
                if not isinstance(tool, dict) or not isinstance(tool.get('name'), str) or not tool['name']:
                    raise ProbeError('invalid tool descriptor')
                schema = tool.get('inputSchema')
                if not isinstance(schema, dict) or schema.get('type') != 'object':
                    raise ProbeError('tool inputSchema must describe an object')
                if tool['name'] in names:
                    raise ProbeError('duplicate tool name across discovery pages')
                names.add(tool['name'])
            count += len(tools)
            cursor = result.get('nextCursor')
            if cursor is None:
                self.tool_count = count
                self.log('tools: ' + str(count))
                return
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise ProbeError('invalid or repeated pagination cursor')
            seen.add(cursor)
        raise ProbeError('tools/list exceeds 10-page bound; discovery incomplete')


def positive_timeout(value):
    try:
        value = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError('timeout must be a number') from None
    if not 0 < value <= 60:
        raise argparse.ArgumentTypeError('timeout must be between 0 and 60 seconds')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='authorized Streamable HTTP MCP endpoint')
    parser.add_argument('--timeout', type=positive_timeout, default=10)
    parser.add_argument('--protocol-version', choices=VERSIONS, default='2025-06-18')
    parser.add_argument('--token-env', metavar='ENV_NAME', help='read a bearer token from this environment variable')
    parser.add_argument('--json', action='store_true', help='emit one sanitized JSON report on stdout')
    args = parser.parse_args(argv)
    probe = None
    error = None
    code = None
    status = 1
    try:
        url = urllib.parse.urlsplit(args.url)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.fragment:
            raise ProbeError('use an HTTP(S) endpoint without embedded credentials or fragments')
        token = None
        if args.token_env:
            token = os.environ.get(args.token_env)
            if not token or any(ord(c) < 0x21 or ord(c) > 0x7e for c in token):
                raise ProbeError('token environment variable is missing, empty, or invalid')
            if url.scheme != 'https' and url.hostname not in ('localhost', '127.0.0.1', '::1'):
                raise ProbeError('bearer authentication requires HTTPS except on loopback')
        probe = Probe(args.url, args.timeout, token, json_output=args.json)
        probe.run(args.protocol_version)
        status = 0
    except (ProbeError, ValueError) as e:
        error = str(e) if isinstance(e, ProbeError) else 'invalid endpoint URL'
        code = 'discovery_failed' if probe else 'configuration_error'
    except KeyboardInterrupt:
        error, code = 'interrupted', 'interrupted'
    if args.json:
        print(json.dumps({
            'schema_version': '1.0', 'status': 'pass' if status == 0 else 'fail',
            'exit_code': status, 'requested_protocol_version': args.protocol_version,
            'negotiated_protocol_version': probe.version if probe else None,
            'session_present': bool(probe.session) if probe else None,
            'tools_advertised': probe.tools_advertised if probe else None,
            'tool_count': probe.tool_count if probe else None,
            'tools_executed': False, 'requests': probe.events if probe else [],
            'error': {'code': code, 'method': probe.active_method if probe else None,
                      'message': error} if error else None,
        }, sort_keys=True))
    else:
        print('FAIL: ' + error if error else 'PASS: bounded discovery completed. No tools were executed.')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
