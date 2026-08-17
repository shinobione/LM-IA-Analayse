import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../js/semantic-bootstrap.js', import.meta.url), 'utf8');
const loader = fs.readFileSync(new URL('../js/loader.js', import.meta.url), 'utf8');
const diagnostic = fs.readFileSync(new URL('../js/neural-diagnostics-v353.js', import.meta.url), 'utf8');

const diagnosticLoad = source.indexOf('const diagnosticReady = await loadDiagnosticProbe();');
const helperLoad = source.indexOf('const helperReady = await loadOptionalHelper();');
const buttonGuard = source.indexOf("if (document.getElementById('semantic-arrangement-btn'))");

assert.ok(diagnosticLoad >= 0, 'bootstrap must explicitly await the read-only Neural diagnostic probe');
assert.ok(helperLoad >= 0, 'bootstrap must explicitly await the semantic helper');
assert.ok(buttonGuard >= 0, 'bootstrap must keep the existing semantic button guard');
assert.ok(
  diagnosticLoad < helperLoad && helperLoad < buttonGuard,
  'diagnostic probe and semantic helper must load BEFORE the early semantic-button return',
);

assert.match(source, /REQUIRED_HELPER_VERSION\s*=\s*'3\.4'/);
assert.match(source, /ASSET_REVISION\s*=\s*'3\.4\.0'/);
assert.match(source, /DIAGNOSTIC_REVISION\s*=\s*'3\.5\.3'/);
assert.match(source, /neural-diagnostics-v353\.js\?v=\$\{DIAGNOSTIC_REVISION\}/);
assert.match(source, /semantic-v32\.js\?v=\$\{ASSET_REVISION\}/);
assert.match(source, /semantic-client\.js\?v=\$\{ASSET_REVISION\}/);
assert.match(source, /cache:\s*'no-store'/);
assert.match(source, /window\.LMNSemanticV32\?\.version\s*===\s*REQUIRED_HELPER_VERSION/);
assert.match(source, /dataset\.sonictraceSemanticHelper/);
assert.match(source, /dataset\.sonictraceNeuralDiagnostic/);
assert.match(loader, /js\/semantic-bootstrap\.js\?v=8/);
assert.match(loader, /sonictraceLoader\s*=\s*'v3\.5\.3-diagnostic'/);

// Parse the browser module for syntax without executing DOM-dependent code.
new Function(diagnostic);
assert.match(diagnostic, /response\.clone\(\)\.json\(\)/, 'probe must read a cloned response, not consume the real response');
assert.match(diagnostic, /analysis\.styles/, 'probe must expose raw CLAP style rows');
assert.match(diagnostic, /ensemble\.styles/, 'probe must expose CLAP + Discogs ensemble rows');
assert.match(diagnostic, /coherence\.family_cluster/, 'probe must expose the V3.5.2 family cluster decision');
assert.match(diagnostic, /ensemble\.decision/, 'probe must expose the ensemble decision reason');
assert.match(diagnostic, /metadata TXT/i, 'probe must state that TXT metadata does not alter inference');
assert.doesNotMatch(diagnostic, /latestPayload\s*=\s*response\.json/, 'probe must never consume the live response directly');

console.log('Semantic V3.5.3 bootstrap + read-only Neural diagnostic probe regression: PASS');
