import assert from 'node:assert/strict';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import * as kernel from '../js/catalog-projection-kernel.mjs';
import { extractKernel, sourceCommit, sourceCommitPath } from './build107-source.mjs';
const revive = (_, v) => v && typeof v === 'object' && 'number' in v ? Number(v.number) : v;
const baseline = JSON.parse(fs.readFileSync('scripts/fixtures/build107-baseline.json', 'utf8'), revive);
for (const test of baseline.cases) {
  const before = structuredClone(test.args);
  assert.deepEqual(kernel[test.fn](...test.args), test.expected, test.name);
  assert.deepEqual(kernel[test.fn](...test.args), test.expected, `${test.name}: repeatability`);
  assert.deepEqual(test.args, before, `${test.name}: no mutation`);
}
assert.deepEqual(Object.keys(kernel).sort(), ['dot', 'normalize', 'powerComponent']);
const pinned = execFileSync('git', ['-c', 'safe.directory=*', 'show', `${sourceCommit}:${sourceCommitPath}`], {encoding:'utf8'});
assert.equal(fs.readFileSync('js/catalog-projection-kernel.mjs','utf8'), extractKernel(pinned), 'Exact extraction from pinned commit');
assert.equal(createHash('sha256').update(fs.readFileSync('js/catalog-projection-kernel.mjs')).digest('hex'), 'f883aa12011d0714049717c6de6a426fbc7c8296a5aa872a978aaeefc47f34d8', 'Build107 distribution pin');
const implementations = fs.readdirSync('js', {recursive:true}).filter(file => /\.(?:js|mjs)$/.test(file) && /\* 37 \+ 11/.test(fs.readFileSync(`js/${file}`,'utf8')));
assert.deepEqual(implementations, ['catalog-projection-kernel.mjs'], 'Exactly one production solver');
const consumer = fs.readFileSync('js/catalog-similarity.js','utf8');
assert.match(consumer, /import \{ normalize, dot, powerComponent \} from '\.\/catalog-projection-kernel.mjs'/);
assert.doesNotMatch(consumer, /function (?:normalize|dot|powerComponent)\(/);
assert.doesNotMatch(consumer, /iter < 42|i \* 37/);
globalThis.window = {};
const events = [];
globalThis.document = {dispatchEvent: event => events.push(event.type)};
await import('../js/catalog-similarity.js');
assert.deepEqual(events, ['sonictrace:similarity-ready']);
for (const {tracks, expected} of baseline.sonicCatalogs) {
  const before = structuredClone(tracks);
  assert.deepEqual(window.SonicTraceCatalog.similarity.analyzeCatalog(tracks), expected);
  assert.deepEqual(tracks, before);
}
console.log(`PASS Build107: ${baseline.cases.length} exact kernel cases, pinned extraction, ${baseline.sonicCatalogs.length} whole catalogs and module ready event.`);
