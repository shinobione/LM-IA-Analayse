import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync('js/catalog-style-families.js', 'utf8');
const durable = fs.readFileSync('js/catalog-style-families-build04.js', 'utf8');
const visual = fs.readFileSync('js/catalog-family-language-build05.js', 'utf8');
const css = fs.readFileSync('css/catalog-style-families.css', 'utf8');
const visualCss = fs.readFileSync('css/catalog-family-language-build05.css', 'utf8');
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
  'function acousticStat(root)',
  "root.querySelector('[data-acoustic-zones=\"true\"]')",
  "statByLabel(root, 'Zones acoustiques')",
  "setText(acoustic.querySelector('span'), 'Zones acoustiques')",
  "setText(styleStat.querySelector('span'), 'Familles sonores')",
  'NS.styleFamilies.analyze(tracks)',
  "target?.id === 'st-catalog-stats'",
  "target?.id === 'st-cluster-legend'",
  'Genres Neural consolidés — distincts des zones acoustiques CLAP',
  'function zoneName(index)',
  'Zone acoustique ${name}',
  'panel.dataset.familySignature',
]) assert.ok(durable.includes(marker), `Build 04/05 durable family renderer is missing ${marker}.`);

for (const marker of [
  "'hip-hop-trap': '#55e2b2'",
  "'bass-dubstep': '#4caeff'",
  "'genre-synthwave': '#9b6cff'",
  "'rnb-soul': '#d85bd4'",
  "'pop-electronic-pop': '#ff667f'",
  'function primaryFamily(trackId, result)',
  "setText(families.querySelector('span'), 'Familles sonores')",
  "setText(head.querySelector('span'), 'Position = proximité CLAP • couleur = famille sonore')",
  'point.dataset.familyId = familyId',
  'row.style.setProperty(\'--family-color\', color)',
  'dot.dataset.familyId = familyId',
  'button.dataset.acousticZone = name',
  'Zone acoustique ${name}',
  'relie $1 zones acoustiques',
  'families.dataset.familySignature',
  'NS.familyVisualLanguage = { colorFor',
]) assert.ok(visual.includes(marker), `Build 05 family visual-language guard is missing ${marker}.`);

for (const marker of [
  '.st-style-family-panel{',
  '.st-style-family-grid{',
  '.st-style-family-card{',
  'grid-template-columns:repeat(6,minmax(0,1fr))',
]) assert.ok(css.includes(marker), `Build 03/04 style-family presentation is missing ${marker}.`);

for (const marker of [
  '.st-map-point[data-family-id] circle{',
  '.st-track-list .st-cluster-dot[data-family-id]',
  '#st-cluster-legend button[data-acoustic-zone]',
  'background:var(--family-color)!important',
]) assert.ok(visualCss.includes(marker), `Build 05 family color CSS is missing ${marker}.`);

for (const marker of [
  'css/catalog-style-families.css?v=2',
  'css/catalog-family-language-build05.css?v=1',
  "['js/catalog-style-families.js?v=2', 'styleFamilies']",
  "['js/catalog-style-families-build04.js?v=1', 'styleFamiliesBuild04']",
  "['js/catalog-family-language-build05.js?v=1', 'familyLanguageBuild05']",
  'js/catalog-similarity.js?v=2',
  'js/catalog-ui.js?v=2',
]) assert.ok(loader.includes(marker), `Build 05 catalog loader is missing ${marker}.`);

assert.ok(similarity.includes('Math.round(Math.sqrt(n / 2))'), 'Build 05 must preserve the existing acoustic K-means ancestry instead of silently redefining acoustic zones as genres.');
assert.ok(!source.includes('Math.round(Math.sqrt(n / 2))'), 'Style families must not reuse the acoustic K-means cluster-count heuristic.');
assert.ok(!source.includes('moods'), 'Style-family taxonomy must be genre-derived, not mood-derived.');
assert.ok(!durable.includes('moods'), 'Durable family renderer must not manufacture style families from moods.');
assert.ok(!visual.includes('analysis?.clusters?.assignments'), 'Build 05 family colors must not be derived from acoustic cluster assignments.');
assert.ok(!visual.includes('moods'), 'Build 05 visual language must not manufacture family colors from moods.');
assert.ok(!durable.includes('Zone acoustique ${index + 1} · ${raw}'), 'Durable renderer must not restore genre/mood-looking acoustic zone labels.');

console.log('SonicTrace Build 05 preserves CLAP acoustic zones while using stable Neural family colors across the catalog UI without observer ping-pong.');
