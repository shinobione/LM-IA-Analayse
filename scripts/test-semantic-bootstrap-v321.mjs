import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../js/semantic-bootstrap.js', import.meta.url), 'utf8');

const helperLoad = source.indexOf('const helperReady = await loadOptionalHelper();');
const buttonGuard = source.indexOf("if (document.getElementById('semantic-arrangement-btn'))");

assert.ok(helperLoad >= 0, 'bootstrap must explicitly await the V3.2 helper');
assert.ok(buttonGuard >= 0, 'bootstrap must keep the existing semantic button guard');
assert.ok(
  helperLoad < buttonGuard,
  'V3.2 helper must load BEFORE the early semantic-button return, otherwise unified/human UI boot order can silently fall back to V3.1',
);

assert.match(source, /semantic-v32\.js\?v=3\.2\.1/);
assert.match(source, /semantic-client\.js\?v=3\.2\.1/);
assert.match(source, /cache:\s*'no-store'/);

console.log('Semantic V3.2.1 bootstrap ordering regression: PASS');
