import assert from 'node:assert/strict';
import fs from 'node:fs';

const js = fs.readFileSync('js/readability-overhaul.js', 'utf8');
const css = fs.readFileSync('css/readability-overhaul.css', 'utf8');
const unifiedJs = fs.readFileSync('js/unified-analysis.js', 'utf8');
const unifiedCss = fs.readFileSync('css/unified-analysis.css', 'utf8');
const loader = fs.readFileSync('js/loader.js', 'utf8');
const readme = fs.readFileSync('README.md', 'utf8');
const styles = fs.readFileSync('js/catalog-style-families.js', 'utf8');
const durable = fs.readFileSync('js/catalog-style-families-build04.js', 'utf8');

for (const marker of [
  "version: 'V2-E'",
  "build: '04'",
  "display: 'V2-E · BUILD 04'",
  "label.className = 'brand-release'",
  "dataset.sonictraceRelease = 'v2-e-build-04'",
]) assert.ok(js.includes(marker), `SonicTrace release runtime is missing ${marker}.`);

assert.ok(css.includes('.sonictrace-readable .brand-release{'), 'SonicTrace release label must have explicit readable header styling.');
assert.ok(readme.includes('V2-E · BUILD 04'), 'README must document the visible SonicTrace release marker.');

for (const marker of [
  "shell.dataset.layout = 'build-02-workflow'",
  'class="unified-intake-row"',
  'data-unified-audio-slot',
  'data-unified-lyrics-slot',
  'Choisis le niveau d’analyse',
  'audioSlot?.appendChild(choose)',
  'lyricsSlot?.appendChild(lyrics)',
]) assert.ok(unifiedJs.includes(marker), `Build 02 unified workflow ancestry is missing ${marker}.`);

for (const marker of [
  '.unified-intake-row{',
  '.unified-intake-slot{',
  'grid-template-columns:repeat(2,minmax(0,1fr))',
  '.unified-analysis-kicker',
  '@media(max-width:900px)',
]) assert.ok(unifiedCss.includes(marker), `Build 02 unified workflow styling is missing ${marker}.`);

for (const marker of [
  "css/unified-analysis.css?v=2",
  "js/unified-analysis.js?v=2",
  "css/readability-overhaul.css?v=4",
  "js/readability-overhaul.js?v=4",
  "css/catalog-style-families.css?v=2",
  "js/catalog-style-families.js?v=2",
  "js/catalog-style-families-build04.js?v=1",
]) assert.ok(loader.includes(marker), `Build 04 cache-bust/runtime load is missing ${marker}.`);

for (const marker of [
  "label:'Hip-Hop / Trap'",
  "label:'R&B / Soul'",
  "label:'Bass / Dubstep'",
  "label:'Pop / Electronic Pop'",
  "label.textContent = 'Zones acoustiques'",
  'Familles stylistiques',
]) assert.ok(styles.includes(marker), `Build 03 catalog taxonomy ancestry is missing ${marker}.`);

for (const marker of [
  "statByLabel(root, 'Familles sonores')",
  "label.textContent = 'Zones acoustiques'",
  'NS.styleFamilies.analyze(tracks)',
  'record.target',
  "target?.id === 'st-catalog-stats'",
  'Familles stylistiques',
  'Hip-Hop / Trap',
]) {
  if (marker === 'Hip-Hop / Trap') assert.ok(styles.includes(marker), `Build 04 taxonomy source is missing ${marker}.`);
  else assert.ok(durable.includes(marker), `Build 04 durable catalog render is missing ${marker}.`);
}

assert.ok(js.includes("actionRoot.querySelector('.st-toolbox')?.remove()"), 'Readability layer must yield toolbox ownership to the unified workflow.');
assert.ok(js.includes("document.querySelector('#unified-analysis-shell .unified-expert-buttons')"), 'Readability layer must preserve unified advanced tools.');

console.log('SonicTrace V2-E · BUILD 04 release marker, Build 02 workflow ancestry and durable style-family taxonomy guard passed.');
