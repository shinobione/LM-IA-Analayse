import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync('js/catalog-style-families.js', 'utf8');
const durable = fs.readFileSync('js/catalog-style-families-build04.js', 'utf8');
const css = fs.readFileSync('css/catalog-style-families.css', 'utf8');
const loader = fs.readFileSync('js/loader.js', 'utf8');
const similarity = fs.readFileSync('js/catalog-similarity.js', 'utf8');

for (const marker of [
  "label:'Hip-Hop / Trap'",
  "label:'R&B / Soul'",
  "label:'Bass / Dubstep'",
  "label:'Pop / Electronic Pop'",
  "label:'Electronic'",
  'function genreEvidence(track)',
  'Array.isArray(track?.neural?.genres)',
  'function analyze(tracks)',
  "label.textContent = 'Zones acoustiques'",
  "note.textContent = 'clusters de proximité CLAP'",
  'Familles stylistiques',
  'genres Neural consolidés',
  'NS.styleFamilies = { analyze',
]) assert.ok(source.includes(marker), `Build 03 style-family ancestry is missing ${marker}.`);

for (const marker of [
  "statByLabel(root, 'Familles sonores')",
  "statByLabel(root, 'Zones acoustiques')",
  "label.textContent = 'Zones acoustiques'",
  "note.textContent = 'clusters de proximité CLAP'",
  'NS.styleFamilies.analyze(tracks)',
  "target?.id === 'st-catalog-stats'",
  "target?.id === 'st-cluster-legend'",
  'Familles stylistiques',
  'Genres Neural consolidés',
  'Zone acoustique ${index + 1}',
]) assert.ok(durable.includes(marker), `Build 04 durable style-family renderer is missing ${marker}.`);

for (const marker of [
  '.st-style-family-panel{',
  '.st-style-family-grid{',
  '.st-style-family-card{',
  'grid-template-columns:repeat(6,minmax(0,1fr))',
]) assert.ok(css.includes(marker), `Build 03/04 style-family presentation is missing ${marker}.`);

for (const marker of [
  'css/catalog-style-families.css?v=2',
  "['js/catalog-style-families.js?v=2', 'styleFamilies']",
  "['js/catalog-style-families-build04.js?v=1', 'styleFamiliesBuild04']",
  'js/catalog-similarity.js?v=2',
  'js/catalog-ui.js?v=2',
]) assert.ok(loader.includes(marker), `Build 04 catalog loader is missing ${marker}.`);

assert.ok(similarity.includes('Math.round(Math.sqrt(n / 2))'), 'Build 04 must preserve the existing acoustic K-means ancestry instead of silently redefining clusters as styles.');
assert.ok(!source.includes('Math.round(Math.sqrt(n / 2))'), 'Style families must not reuse the acoustic K-means cluster-count heuristic.');
assert.ok(!source.includes('moods'), 'Style-family taxonomy must be genre-derived, not mood-derived.');
assert.ok(!durable.includes('moods'), 'Build 04 durable renderer must not manufacture style families from moods.');

console.log('SonicTrace Build 04 keeps acoustic CLAP zones and Neural style families distinct across native catalog rerenders.');
