import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../js/semantic-bootstrap.js', import.meta.url), 'utf8');
const loader = fs.readFileSync(new URL('../js/loader.js', import.meta.url), 'utf8');
const diagnostic = fs.readFileSync(new URL('../js/neural-diagnostics-v353.js', import.meta.url), 'utf8');

const debugCheck = source.indexOf('const debugEnabled = neuralDebugEnabled();');
const diagnosticLoad = source.indexOf('const diagnosticReady = debugEnabled ? await loadDiagnosticProbe() : false;');
const helperLoad = source.indexOf('const helperReady = await loadOptionalHelper();');
const buttonGuard = source.indexOf("if (document.getElementById('semantic-arrangement-btn'))");

assert.ok(debugCheck >= 0, 'bootstrap must explicitly decide whether Neural debug mode is enabled');
assert.ok(diagnosticLoad >= 0, 'bootstrap must gate the read-only Neural diagnostic probe behind debug mode');
assert.ok(helperLoad >= 0, 'bootstrap must explicitly await the semantic helper');
assert.ok(buttonGuard >= 0, 'bootstrap must keep the existing semantic button guard');
assert.ok(
  debugCheck < diagnosticLoad && diagnosticLoad < helperLoad && helperLoad < buttonGuard,
  'debug gate, optional diagnostic probe and semantic helper must be resolved before the semantic-button return',
);

assert.match(source, /REQUIRED_HELPER_VERSION\s*=\s*'3\.4'/);
assert.match(source, /ASSET_REVISION\s*=\s*'3\.4\.0'/);
assert.match(source, /DIAGNOSTIC_REVISION\s*=\s*'3\.5\.3\.1'/);
assert.match(source, /params\.get\('debug'\)/);
assert.match(source, /debug\.includes\('neural'\)/);
assert.match(source, /3\.5\.3\.1-diagnostic/);
assert.match(source, /neural-diagnostics-v353\.js\?v=\$\{DIAGNOSTIC_REVISION\}/);
assert.match(source, /semantic-v32\.js\?v=\$\{ASSET_REVISION\}/);
assert.match(source, /semantic-client\.js\?v=\$\{ASSET_REVISION\}/);
assert.match(source, /cache:\s*'no-store'/);
assert.match(source, /window\.LMNSemanticV32\?\.version\s*===\s*REQUIRED_HELPER_VERSION/);
assert.match(source, /dataset\.sonictraceSemanticHelper/);
assert.match(source, /dataset\.sonictraceNeuralDiagnostic/);
assert.match(source, /:\s*'off'/, 'normal runtime must explicitly mark the Neural diagnostic as off');
assert.match(loader, /js\/semantic-bootstrap\.js\?v=9/);

new Function(diagnostic);
assert.match(diagnostic, /response\.clone\(\)\.json\(\)/, 'probe must read a cloned response, not consume the real response');
assert.match(diagnostic, /analysis\.styles/, 'probe must expose raw CLAP style rows');
assert.match(diagnostic, /ensemble\.styles/, 'probe must expose CLAP + Discogs ensemble rows');
assert.match(diagnostic, /coherence\.family_cluster/, 'probe must expose the family cluster decision');
assert.match(diagnostic, /ensemble\.decision/, 'probe must expose the ensemble decision reason');
assert.match(diagnostic, /semantic-context-tags/, 'probe must anchor immediately after visible Neural style badges');
assert.match(diagnostic, /insertAdjacentElement\('afterend', panel\)/, 'probe must be inserted after the Neural badges, not buried at card bottom');
assert.match(diagnostic, /PAYLOAD CAPTURÉ/, 'probe must visibly confirm that the real payload was captured when debug mode is enabled');
assert.match(diagnostic, /metadata|TXT/i, 'probe must state that TXT metadata does not alter inference');
assert.doesNotMatch(diagnostic, /latestPayload\s*=\s*response\.json/, 'probe must never consume the live response directly');

console.log('Semantic V3.5.5 stable diagnostic gate regression: PASS');
