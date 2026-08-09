import assert from 'node:assert/strict';
import fs from 'node:fs';

const js = fs.readFileSync('js/readability-overhaul.js', 'utf8');
const css = fs.readFileSync('css/readability-overhaul.css', 'utf8');
const readme = fs.readFileSync('README.md', 'utf8');

for (const marker of [
  "version: 'V2-E'",
  "build: '01'",
  "display: 'V2-E · BUILD 01'",
  "label.className = 'brand-release'",
  "dataset.sonictraceRelease = 'v2-e-build-01'",
]) assert.ok(js.includes(marker), `SonicTrace release runtime is missing ${marker}.`);

assert.ok(css.includes('.sonictrace-readable .brand-release{'), 'SonicTrace release label must have explicit readable header styling.');
assert.ok(readme.includes('V2-E · BUILD 01'), 'README must document the visible SonicTrace release marker.');

console.log('SonicTrace V2-E · BUILD 01 visible release marker guard passed.');
