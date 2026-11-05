import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const cli = resolve('bin/naif-mcp-doctor.mjs');
const example = (status) => ({
  schema_version: '1.0', status, exit_code: status === 'pass' ? 0 : 1,
  requested_protocol_version: '2025-06-18',
  negotiated_protocol_version: status === 'pass' ? '2025-11-25' : null,
  session_present: status === 'pass',
  tools_advertised: status === 'pass' ? true : null,
  tool_count: status === 'pass' ? 2 : null,
  tools_executed: false,
  requests: [{method: 'initialize', http_status: 200}],
  error: status === 'pass' ? null : {code: 'discovery_failed',
    method: 'initialize', message: 'mismatched request ID or invalid response shape'}
});
function execute(args, input) {
  return spawnSync(process.execPath, [cli, ...args], {
    encoding: 'utf8', input, timeout: 20000, maxBuffer: 1048576
  });
}
test('healthy report stays free and offline', () => {
  const p = execute(['--report', '-', '--format', 'json',
    '--show-optional-service'], JSON.stringify(example('pass')));
  assert.equal(p.status, 0, p.stderr);
  const output = JSON.parse(p.stdout);
  assert.equal(output.product, 'NAIF Error Passport');
  assert.equal(output.category, 'healthy');
  assert.equal(output.automatic_payment, false);
  assert.equal(output.automatic_repair, false);
  assert.equal(output.optional_service, undefined);
});
test('failed report is diagnosis-only, not a repair', () => {
  const p = execute(['--report', '-', '--format', 'json'], JSON.stringify(example('fail')));
  assert.equal(p.status, 1, p.stderr);
  assert.equal(JSON.parse(p.stdout).result, 'DIAGNOSIS_ONLY');
});
test('probe requires explicit endpoint authorization', () => {
  const p = execute(['--probe', 'https://example.invalid/mcp']);
  assert.equal(p.status, 2);
  assert.match(p.stderr, /requires --authorized/);
});
test('secret-bearing extra fields never appear in the output', () => {
  const report = {...example('fail'), untrusted: {
    token: 'DO_NOT_PRINT_SECRET_12345'}};
  const p = execute(['--report', '-', '--format', 'json'], JSON.stringify(report));
  assert.equal(p.status, 1);
  assert.ok(!p.stdout.includes('DO_NOT_PRINT_SECRET_12345'));
  assert.ok(!p.stderr.includes('DO_NOT_PRINT_SECRET_12345'));
});
