// Run before extraction only. Reads both original consumers; never supplies runtime code.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { stripTypeScriptTypes } from 'node:module';
import vm from 'node:vm';

const sonic = fs.readFileSync('js/catalog-similarity.js', 'utf8');
const studio = stripTypeScriptTypes(fs.readFileSync('../shinobiwan-studio/src/catalog-intelligence.ts', 'utf8'));
function extract(source, name) {
  const start = source.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `Original ${name} must exist; do not recapture after extraction`);
  const body = source.indexOf('{', start);
  let depth = 1, end = body + 1;
  while (depth) { const char = source[end++]; if (char === '{') depth++; if (char === '}') depth--; }
  return source.slice(start, end);
}
function numerical(source, normalization) {
  return new Function(`${['dot', normalization, 'powerComponent'].map(name => extract(source, name)).join('\n')}; return { normalize: ${normalization}, dot, powerComponent };`)();
}
const a = numerical(sonic, 'normalize'), b = numerical(studio, 'normalizeVector');
const vectors = [[], [0, 0, 0], [3, 4], [-0, 0], [1e-160, -1e-160], [1e160, -1e160]];
const matrices = [[], [[]], [[0, 0], [0, 0]], [[1, 2], [1, 2]], [[1, 2], [2, 4], [-3, -6]], [[1, 0, 1], [0, 1, 1], [1, 1, 2]], [[.3, -.8, .1], [.7, .2, -.6], [-.4, .9, .5]], Array.from({length: 7}, (_, r) => Array.from({length: 512}, (_, i) => ((i * 17 + r * 31) % 103 - 51) / 53))];
const cases = [];
for (const vector of vectors) cases.push({name: `normalize ${cases.length}`, fn: 'normalize', args: [vector]});
for (const args of [[[], []], [[1, 2, 3], [4]], [[4], [1, 2, 3]], [[1, 2], [1, 2]]]) cases.push({name: `dot ${cases.length}`, fn: 'dot', args});
for (const [index, rows] of matrices.entries()) {
  cases.push({name: `PC1 matrix ${index}`, fn: 'powerComponent', args: [rows, null]});
  cases.push({name: `PC2 matrix ${index}`, fn: 'powerComponent', args: [rows, a.powerComponent(rows, null)]});
}
// Preserve signed zero and non-finite numbers exactly in the JSON oracle.
const encode = value => JSON.stringify(value, (_, v) => typeof v === 'number' && (Object.is(v, -0) || !Number.isFinite(v)) ? {number: String(Object.is(v, -0) ? '-0' : v)} : v);
for (const test of cases) {
  const before = encode(test.args);
  const expected = a[test.fn](...test.args);
  assert.deepEqual(b[test.fn](...test.args), expected, test.name);
  assert.equal(encode(test.args), before, `${test.name}: mutation`);
  test.expected = expected;
}
const window = {};
vm.runInNewContext(sonic, {window, document: {dispatchEvent() {}}, CustomEvent: class {}});
const studioModule = await import(`data:text/javascript;base64,${Buffer.from(studio).toString('base64')}`);
const catalogs = matrices.map(rows => rows.map((vector, i) => ({id: `track-${i}`, title: `Track ${i}`, neural: {embedding: {vector}}})));
catalogs.push([{id:'missing-a'}, {id:'missing-b'}]);
const sonicCatalogs = catalogs.map(tracks => ({tracks, expected: window.SonicTraceCatalog.similarity.analyzeCatalog(tracks)}));
const studioCatalogs = matrices.map(rows => rows.map((vector, i) => ({trackId:`track-${i}`, title:`Track ${i}`, embedding:{dimension:512, model:'clap', vector}, semanticSummary:null})) ).map(entries => ({entries, expected:studioModule.analyzeCatalog(entries)}));
fs.mkdirSync('scripts/fixtures', {recursive:true});
fs.writeFileSync('scripts/fixtures/build107-baseline.json', encode({cases, sonicCatalogs, studioCatalogs}) + '\n');
console.log(`PASS: ${cases.length} exact cross-implementation numerical cases; ${sonicCatalogs.length} SonicTrace and ${studioCatalogs.length} Studio whole-catalog baselines captured before extraction.`);
