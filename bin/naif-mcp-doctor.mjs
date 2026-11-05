#!/usr/bin/env node
/**
 * Thin, dependency-free launcher for the EXISTING tested Python Error Passport.
 * Requires Python 3.10+ on PATH. Does not upload reports, call npm APIs,
 * initiate network probes or start payments. All network probing still
 * requires the explicit --probe URL --authorized arguments.
 */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const script = resolve(dirname(fileURLToPath(import.meta.url)), '../tools/error_passport.py');
const args = process.argv.slice(2);
const python = process.platform === 'win32' ? 'python' : 'python3';
const child = spawnSync(python, [script, ...args], {
  shell: false,
  windowsHide: true,
  stdio: 'inherit',
  timeout: 310000
});
if (child.error) {
  if (child.error.code === 'ENOENT') {
    console.error('NAIF MCP Doctor requires Python 3.10+ on PATH. No report was sent.');
  } else {
    console.error('NAIF MCP Doctor could not launch the local Python diagnostic.');
  }
  process.exitCode = 2;
} else if (child.signal) {
  console.error('NAIF MCP Doctor was interrupted before completing.');
  process.exitCode = 2;
} else {
  process.exitCode = child.status ?? 2;
}
