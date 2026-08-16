import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../js/semantic-bootstrap.js', import.meta.url), 'utf8');

const helperLoad = source.indexOf('const helperReady = await loadOptionalHelper();');
const buttonGuard = source.indexOf("if (document.getElementById('semantic-arrangement-btn'))");

assert.ok(helperLoad >= 0, 'bootstrap must explicitly await the semantic helper');
assert.ok(buttonGuard >= 0, 'bootstrap must keep the existing semantic button guard');
assert.ok(
  helperLoad < buttonGuard,
  'semantic helper must load BEFORE the early semantic-button return, otherwise unified/human UI boot order can silently fall back',
);

assert.match(source, /REQUIRED_HELPER_VERSION\s*=\s*'3\.3'/);
assert.match(source, /semantic-v32\.js\?v=3\.3/);
assert.match(source, /semantic-client\.js\?v=3\.2\.1/);
assert.match(source, /cache:\s*'no-store'/);
assert.match(source, /window\.LMNSemanticV32\?\.version\s*===\s*REQUIRED_HELPER_VERSION/);

console.log('Semantic V3.3 bootstrap ordering + version regression: PASS');
